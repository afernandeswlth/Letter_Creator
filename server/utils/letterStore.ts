/**
 * Letter history store (Supabase) — Nitro/local-dev mirror of engine/store.py.
 *
 * Records each generated letter's metadata in a Supabase Postgres table and
 * uploads the PDF to a Supabase Storage bucket, so the dashboard's Recent
 * Letters can list and re-download them. Best-effort and fail-safe: if Supabase
 * isn't configured (or a call fails), we log and carry on — persistence must
 * never break letter delivery. Production uses the Python twin; keep them in sync.
 *
 * Env (server-side only): SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
 * SUPABASE_LETTERS_TABLE (default 'letters'), SUPABASE_LETTERS_BUCKET (default 'letters').
 */
import { randomUUID } from 'node:crypto'

export const LABELS: Record<string, string> = {
  welcome: 'Welcome Letter',
  approval: 'Formal Approval Letter',
  commencement: 'Commencement Letter',
  'pre-approval': 'Pre-Approval Letter',
  'conditional-approval': 'Conditional Approval Letter',
  discharge: 'Discharge Confirmation Letter',
  custom: 'Custom Letter',
}

interface Cfg { url: string; key: string; table: string; bucket: string }

function cfg(): Cfg | null {
  const url = (process.env.SUPABASE_URL || '').replace(/\/+$/, '')
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || ''
  if (!url || !key) return null
  return {
    url,
    key,
    table: process.env.SUPABASE_LETTERS_TABLE || 'letters',
    bucket: process.env.SUPABASE_LETTERS_BUCKET || 'letters',
  }
}

export function isConfigured(): boolean {
  return cfg() !== null
}

function headers(c: Cfg, extra?: Record<string, string>): Record<string, string> {
  return { apikey: c.key, Authorization: `Bearer ${c.key}`, ...(extra ?? {}) }
}

function stripTitle(name: string): string {
  return (name || '').trim().replace(/^(mr|mrs|ms|miss|dr)\.?\s+/i, '')
}

export interface LetterMeta {
  letterType: string
  typeLabel?: string
  brand: string
  customer?: string
  reference?: string | null
}

/** Derive display metadata for a form-driven letter from its field values. */
export function formMeta(letterType: string, brand: string, values: Record<string, string>): LetterMeta {
  const v = values || {}
  const customer = (v.borrowers || v.recipientName || v.customerNames || v.builderName || '').trim()
  const reference = (v.loanAccountNumber || v.applicationNumber || v.accountNumbers || '').trim()
  return {
    letterType,
    typeLabel: LABELS[letterType] ?? 'Letter',
    brand,
    customer: stripTitle(customer),
    reference: reference || null,
  }
}

/** Upload the PDF and insert a metadata row. Best-effort; never throws. */
export async function saveLetter(
  meta: LetterMeta,
  pdf: Buffer | Uint8Array,
  filename: string,
  status: string,
): Promise<string | null> {
  const c = cfg()
  if (!c) return null
  try {
    const id = randomUUID()
    const pdfPath = `${id}.pdf`
    const up = await fetch(`${c.url}/storage/v1/object/${c.bucket}/${pdfPath}`, {
      method: 'POST',
      headers: headers(c, { 'Content-Type': 'application/pdf', 'x-upsert': 'true' }),
      body: pdf as unknown as BodyInit,
    })
    if (!up.ok) {
      console.warn('[letterStore] storage upload failed', up.status, (await up.text()).slice(0, 200))
      return null
    }
    const row = {
      id,
      letter_type: meta.letterType,
      type_label: meta.typeLabel ?? LABELS[meta.letterType] ?? 'Letter',
      brand: meta.brand,
      customer: meta.customer || null,
      reference: meta.reference || null,
      status,
      filename,
      pdf_path: pdfPath,
    }
    const ins = await fetch(`${c.url}/rest/v1/${c.table}`, {
      method: 'POST',
      headers: headers(c, { 'Content-Type': 'application/json', Prefer: 'return=minimal' }),
      body: JSON.stringify(row),
    })
    if (!ins.ok) {
      console.warn('[letterStore] row insert failed', ins.status, (await ins.text()).slice(0, 200))
      return null
    }
    return id
  } catch (err) {
    console.warn('[letterStore] saveLetter error', (err as Error).message)
    return null
  }
}

export interface PublicLetter {
  id: string
  letterType: string
  typeLabel: string
  brand: string
  customer: string | null
  reference: string | null
  status: string
  filename: string
  createdAt: string
}

export async function recentLetters(limit = 20): Promise<PublicLetter[]> {
  const c = cfg()
  if (!c) return []
  try {
    const url = new URL(`${c.url}/rest/v1/${c.table}`)
    url.searchParams.set('select', '*')
    url.searchParams.set('order', 'created_at.desc')
    url.searchParams.set('limit', String(limit))
    const r = await fetch(url, { headers: headers(c) })
    if (!r.ok) {
      console.warn('[letterStore] recent select failed', r.status, (await r.text()).slice(0, 200))
      return []
    }
    const rows = (await r.json()) as Record<string, string>[]
    return rows.map((x) => ({
      id: x.id,
      letterType: x.letter_type,
      typeLabel: x.type_label,
      brand: x.brand,
      customer: x.customer ?? null,
      reference: x.reference ?? null,
      status: x.status,
      filename: x.filename,
      createdAt: x.created_at,
    }))
  } catch (err) {
    console.warn('[letterStore] recentLetters error', (err as Error).message)
    return []
  }
}

/** A short-lived download URL for a stored letter's PDF, or null. */
export async function signedUrl(letterId: string, expiresIn = 3600): Promise<string | null> {
  const c = cfg()
  if (!c) return null
  try {
    const url = new URL(`${c.url}/rest/v1/${c.table}`)
    url.searchParams.set('select', 'pdf_path,filename')
    url.searchParams.set('id', `eq.${letterId}`)
    url.searchParams.set('limit', '1')
    const r = await fetch(url, { headers: headers(c) })
    const rows = r.ok ? ((await r.json()) as { pdf_path?: string }[]) : []
    const path = rows[0]?.pdf_path
    if (!path) return null
    const s = await fetch(`${c.url}/storage/v1/object/sign/${c.bucket}/${path}`, {
      method: 'POST',
      headers: headers(c, { 'Content-Type': 'application/json' }),
      body: JSON.stringify({ expiresIn }),
    })
    if (!s.ok) {
      console.warn('[letterStore] sign failed', s.status, (await s.text()).slice(0, 200))
      return null
    }
    const j = (await s.json()) as { signedURL?: string; signedUrl?: string }
    let signed = j.signedURL || j.signedUrl
    if (!signed) return null
    // The API returns "/object/sign/<bucket>/<file>?token=…" without the
    // "/storage/v1" prefix; prepend it to form a fetchable URL.
    if (!signed.startsWith('/storage/v1')) {
      signed = '/storage/v1' + (signed.startsWith('/') ? signed : `/${signed}`)
    }
    return `${c.url}${signed}`
  } catch (err) {
    console.warn('[letterStore] signedUrl error', (err as Error).message)
    return null
  }
}

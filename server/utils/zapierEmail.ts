/**
 * Email drafts via a Zapier "Catch Hook" webhook.
 *
 * Config via env:
 *   ZAPIER_EMAIL_WEBHOOK_URL   the Catch Hook URL from your Zap
 *
 * The app POSTs multipart/form-data (to, subject, body, filename + the PDF file)
 * to the webhook. The Zap's next step ("Gmail → Create Draft", connected to
 * hello@wlth.com) uses those fields, attaching the PDF file. No service account
 * or domain-wide delegation needed.
 */

export function zapierEmailConfig() {
  const url = process.env.ZAPIER_EMAIL_WEBHOOK_URL
  return { configured: Boolean(url), url: url ?? null }
}

export interface ZapierDraftInput {
  to: string
  cc?: string // comma-separated CC recipients
  subject: string
  html: string
  attachments: Array<{ filename: string; content: Buffer }>
  sender?: string // mailbox to draft from (e.g. construction@wlth.com)
}

/** POST the draft details + attachment(s) to a Zapier webhook. Pass `webhookUrl`
 *  to target a specific Zap (e.g. the construction@wlth.com one); defaults to the
 *  shared ZAPIER_EMAIL_WEBHOOK_URL. */
export async function createDraftViaZapier(input: ZapierDraftInput, webhookUrl?: string): Promise<void> {
  const url = webhookUrl || process.env.ZAPIER_EMAIL_WEBHOOK_URL
  if (!url) throw new Error('Zapier email webhook is not configured (set ZAPIER_EMAIL_WEBHOOK_URL).')

  const form = new FormData()
  form.append('to', input.to)
  if (input.cc) form.append('cc', input.cc)
  if (input.sender) form.append('from', input.sender)
  form.append('subject', input.subject)
  form.append('body', input.html)
  form.append('filename', input.attachments[0]?.filename ?? 'Welcome Letter.pdf')
  // The welcome letter is `attachment`; the nomination form (when present) is
  // `attachment2`. Map both in the Zap's Gmail "Attachments" field.
  input.attachments.forEach((att, i) => {
    // Uint8Array copy so the Blob owns a plain ArrayBuffer (not Node's pooled one).
    const blob = new Blob([new Uint8Array(att.content)], { type: 'application/pdf' })
    form.append(i === 0 ? 'attachment' : `attachment${i + 1}`, blob, att.filename)
  })

  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Zapier webhook returned ${res.status}. ${body.slice(0, 200)}`)
  }
}

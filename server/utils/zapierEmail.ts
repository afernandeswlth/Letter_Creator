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
  subject: string
  html: string
  filename: string
  pdf: Buffer
  template: string
}

/** POST the draft details + PDF to the Zapier webhook. */
export async function createDraftViaZapier(input: ZapierDraftInput): Promise<void> {
  const url = process.env.ZAPIER_EMAIL_WEBHOOK_URL
  if (!url) throw new Error('Zapier email webhook is not configured (set ZAPIER_EMAIL_WEBHOOK_URL).')

  const form = new FormData()
  form.append('to', input.to)
  form.append('subject', input.subject)
  form.append('body', input.html)
  form.append('filename', input.filename)
  form.append('template', input.template)
  // Uint8Array copy so the Blob owns a plain ArrayBuffer (not Node's pooled one).
  form.append('attachment', new Blob([new Uint8Array(input.pdf)], { type: 'application/pdf' }), input.filename)

  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Zapier webhook returned ${res.status}. ${body.slice(0, 200)}`)
  }
}

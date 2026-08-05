import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { runEngineFormPdf } from '~~/server/utils/engine'
import { createDraftViaZapier } from '~~/server/utils/zapierEmail'
import { createGmailDraft, gmailConfig } from '~~/server/utils/gmail'
import { formEmail } from '~~/server/utils/emailTemplate'

/** POST /api/forms/email — generate a form letter's PDF and create a Gmail draft. */
export default defineEventHandler(async (event) => {
  const body = await readBody<{
    letterType: string; brand?: string; values?: Record<string, string>
    to?: string; cc?: string; filename?: string
  }>(event)
  const to = body.to?.trim()
  if (!to) throw createError({ statusCode: 400, statusMessage: 'Missing recipient email address' })
  const cc = body.cc?.trim() || undefined

  // Per-letter-type sender mailbox (undefined → the default GMAIL_SENDER).
  const FORM_SENDERS: Record<string, string> = { commencement: 'construction@wlth.com' }
  const sender = FORM_SENDERS[body.letterType]
  // Types with a dedicated sender draft from a separate inbox, so they use their
  // OWN Zap — never the shared (welcome) hook, which would land in the wrong box.
  const FORM_WEBHOOKS: Record<string, string | undefined> = {
    commencement: process.env.ZAPIER_CONSTRUCTION_WEBHOOK_URL,
  }
  const webhookUrl = sender ? FORM_WEBHOOKS[body.letterType] : process.env.ZAPIER_EMAIL_WEBHOOK_URL

  const brand = body.brand ?? 'wlth'
  let pdf: Buffer
  try {
    pdf = await runEngineFormPdf(body.letterType, brand, body.values ?? {})
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }

  const { subject, html } = formEmail(body.letterType, brand, body.values ?? {})
  const attachments = [{ filename: `${(body.filename || 'Letter').trim()}.pdf`, content: pdf }]

  // Commencement emails also attach the brand's Progress Payment Guidelines.
  if (body.letterType === 'commencement') {
    const bKey = brand === 'mma' ? 'mma' : 'wlth'
    const gPath = join(process.cwd(), 'engine', 'assets', bKey, 'progress-payment-guidelines.pdf')
    if (existsSync(gPath)) {
      const gLabel = brand === 'mma' ? 'Mortgage Mart' : 'WLTH'
      attachments.push({ filename: `${gLabel} Progress Payment Guidelines.pdf`, content: readFileSync(gPath) })
    }
  }
  const gmailLink = 'https://mail.google.com/mail/u/0/#drafts'
  // When a specific sender mailbox is required (e.g. construction@wlth.com for
  // commencement), prefer the Gmail service-account path — it natively drafts
  // as that mailbox and adds the Cc header. Otherwise keep Zapier-first.
  const preferGmail = Boolean(sender) && gmailConfig().configured
  try {
    if (preferGmail) {
      const draft = await createGmailDraft({ to, cc, subject, html, attachments, sender })
      return { ok: true, via: 'gmail', ...draft, to, cc, from: sender ?? null }
    }
    if (webhookUrl) {
      await createDraftViaZapier({ to, cc, subject, html, attachments, sender }, webhookUrl)
      return { ok: true, via: 'zapier', link: gmailLink, to, cc, from: sender ?? null }
    }
    if (!sender && gmailConfig().configured) {
      const draft = await createGmailDraft({ to, cc, subject, html, attachments, sender })
      return { ok: true, via: 'gmail', ...draft, to, cc, from: sender ?? null }
    }
    throw new Error(
      sender
        ? 'Commencement email is not configured. Set ZAPIER_CONSTRUCTION_WEBHOOK_URL (or the Gmail service account).'
        : 'Email is not configured. Set ZAPIER_EMAIL_WEBHOOK_URL.',
    )
  } catch (err) {
    throw createError({ statusCode: 502, statusMessage: (err as Error).message })
  }
})

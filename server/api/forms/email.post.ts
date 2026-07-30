import { runEngineFormPdf } from '~~/server/utils/engine'
import { createDraftViaZapier, zapierEmailConfig } from '~~/server/utils/zapierEmail'
import { createGmailDraft, gmailConfig } from '~~/server/utils/gmail'
import { formEmail } from '~~/server/utils/emailTemplate'

/** POST /api/forms/email — generate a form letter's PDF and create a Gmail draft. */
export default defineEventHandler(async (event) => {
  const body = await readBody<{
    letterType: string; brand?: string; values?: Record<string, string>; to?: string; filename?: string
  }>(event)
  const to = body.to?.trim()
  if (!to) throw createError({ statusCode: 400, statusMessage: 'Missing recipient email address' })

  const brand = body.brand ?? 'wlth'
  let pdf: Buffer
  try {
    pdf = await runEngineFormPdf(body.letterType, brand, body.values ?? {})
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }

  const { subject, html } = formEmail(body.letterType, brand, body.values ?? {})
  const attachments = [{ filename: `${(body.filename || 'Letter').trim()}.pdf`, content: pdf }]
  const gmailLink = 'https://mail.google.com/mail/u/0/#drafts'
  try {
    if (zapierEmailConfig().configured) {
      await createDraftViaZapier({ to, subject, html, attachments })
      return { ok: true, via: 'zapier', link: gmailLink, to }
    }
    if (gmailConfig().configured) {
      const draft = await createGmailDraft({ to, subject, html, attachments })
      return { ok: true, via: 'gmail', ...draft, to }
    }
    throw new Error('Email is not configured. Set ZAPIER_EMAIL_WEBHOOK_URL.')
  } catch (err) {
    throw createError({ statusCode: 502, statusMessage: (err as Error).message })
  }
})

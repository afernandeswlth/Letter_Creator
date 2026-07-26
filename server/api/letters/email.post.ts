import { runEnginePdf } from '~~/server/utils/engine'
import { createGmailDraft, gmailConfig } from '~~/server/utils/gmail'
import { createDraftViaZapier, zapierEmailConfig } from '~~/server/utils/zapierEmail'
import { welcomeEmail } from '~~/server/utils/emailTemplate'

/**
 * POST /api/letters/email
 * Multipart: files[] = funder .docx, brand, ddBsb, ddAccount, partyIndex,
 *            to (borrower email), name (recipient), filename (PDF name),
 *            template ('Offset' | 'Standard').
 * Generates the party's PDF and creates a Gmail DRAFT (letter attached) in the
 * GMAIL_SENDER mailbox — it does not send.
 */
export default defineEventHandler(async (event) => {
  const parts = (await readMultipartFormData(event)) ?? []
  const files = parts
    .filter((p) => p.filename && p.name === 'files')
    .map((p) => ({ filename: p.filename as string, data: p.data }))
  const field = (n: string) =>
    parts.find((p) => p.name === n && !p.filename)?.data.toString('utf-8')

  const to = field('to')?.trim()
  if (!files.length) throw createError({ statusCode: 400, statusMessage: 'No .docx files found' })
  if (!to) throw createError({ statusCode: 400, statusMessage: 'Missing borrower email address' })

  const brand = field('brand') ?? 'wlth'
  const template = (field('template') === 'Offset' ? 'Offset' : 'Standard') as 'Offset' | 'Standard'
  const filename = (field('filename') || 'Welcome Letter').trim()

  let pdf: Buffer
  try {
    pdf = await runEnginePdf(files, {
      brand,
      ddBsb: field('ddBsb') ?? '',
      ddAccount: field('ddAccount') ?? '',
      partyIndex: Number(field('partyIndex') ?? '0'),
    })
  } catch (err) {
    throw createError({ statusCode: 500, statusMessage: `Engine error: ${(err as Error).message}` })
  }

  const { subject, html } = welcomeEmail(brand, field('name') || to, template)
  const gmailLink = 'https://mail.google.com/mail/u/0/#drafts'

  try {
    // Prefer Zapier (simplest to set up); fall back to the Gmail service account.
    if (zapierEmailConfig().configured) {
      await createDraftViaZapier({ to, subject, html, filename: `${filename}.pdf`, pdf, template })
      return { ok: true, via: 'zapier', link: gmailLink, to }
    }
    if (gmailConfig().configured) {
      const draft = await createGmailDraft({
        to,
        subject,
        html,
        attachment: { filename: `${filename}.pdf`, content: pdf },
      })
      return { ok: true, via: 'gmail', ...draft, to }
    }
    throw new Error(
      'Email is not configured. Set ZAPIER_EMAIL_WEBHOOK_URL, or the Gmail service account + GMAIL_SENDER.',
    )
  } catch (err) {
    throw createError({ statusCode: 502, statusMessage: (err as Error).message })
  }
})

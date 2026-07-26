import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { runEnginePdf } from '~~/server/utils/engine'
import { createGmailDraft, gmailConfig } from '~~/server/utils/gmail'
import { createDraftViaZapier, zapierEmailConfig } from '~~/server/utils/zapierEmail'
import { welcomeEmail } from '~~/server/utils/emailTemplate'

/**
 * POST /api/letters/email
 * Multipart: files[] = funder .docx, brand, ddBsb, ddAccount, partyIndex,
 *            to, name (borrower), filename (PDF name), offset ('yes'|'no'),
 *            isTrust ('true'|'false'), trustName, accountNumber.
 * Generates the party's PDF, builds the templated email, and creates a Gmail
 * DRAFT (no send). When offset = 'no', the brand's Linked Account Nomination
 * Form is attached as well.
 */
const FORM_NAMES: Record<string, string> = {
  wlth: 'WLTH Linked Account Nomination Form.pdf',
  mma: 'Mortgage Mart Linked Account Nomination Form.pdf',
}

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
  const offset = field('offset') === 'no' ? 'no' : 'yes'
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

  const { subject, html } = welcomeEmail({
    brandId: brand,
    borrowerName: field('name') || to,
    offset,
    isTrust: field('isTrust') === 'true',
    trustName: field('trustName') || '',
    accountNumber: field('accountNumber') || '',
  })

  const attachments = [{ filename: `${filename}.pdf`, content: pdf }]

  // No offset link → also attach the brand's Linked Account Nomination Form.
  if (offset === 'no') {
    try {
      const formPath = join(process.cwd(), 'engine', 'assets', brand, 'nomination-form.pdf')
      const formPdf = await readFile(formPath)
      attachments.push({ filename: FORM_NAMES[brand] ?? 'Linked Account Nomination Form.pdf', content: formPdf })
    } catch (err) {
      throw createError({ statusCode: 500, statusMessage: `Could not read nomination form: ${(err as Error).message}` })
    }
  }

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
    throw new Error(
      'Email is not configured. Set ZAPIER_EMAIL_WEBHOOK_URL, or the Gmail service account + GMAIL_SENDER.',
    )
  } catch (err) {
    throw createError({ statusCode: 502, statusMessage: (err as Error).message })
  }
})

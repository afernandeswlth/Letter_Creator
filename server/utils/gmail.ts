import { readFileSync } from 'node:fs'
import { google } from 'googleapis'

/**
 * Gmail draft creation (service account with domain-wide delegation).
 *
 * Config via env:
 *   GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_APPLICATION_CREDENTIALS  the key
 *   GMAIL_SENDER   the mailbox to create the draft in, e.g. hello@wlth.com
 *
 * The service account's client ID must be granted domain-wide delegation for
 * the scope https://www.googleapis.com/auth/gmail.compose in the Google
 * Workspace admin console, so it can create drafts as GMAIL_SENDER.
 */

const SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

function loadCredentials(): { client_email: string; private_key: string } | null {
  const raw = process.env.GOOGLE_SERVICE_ACCOUNT_JSON
  const path = process.env.GOOGLE_APPLICATION_CREDENTIALS
  try {
    if (raw) return JSON.parse(raw)
    if (path) return JSON.parse(readFileSync(path, 'utf-8'))
  } catch {
    return null
  }
  return null
}

export function gmailConfig() {
  const creds = loadCredentials()
  const sender = process.env.GMAIL_SENDER
  return {
    configured: Boolean(creds?.client_email && creds?.private_key && sender),
    sender: sender ?? null,
  }
}

function b64url(buf: Buffer | string): string {
  return Buffer.from(buf)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
}

function wrap76(s: string): string {
  return s.replace(/.{1,76}/g, '$&\r\n')
}

function encodeSubject(subject: string): string {
  // RFC 2047 encoded-word so non-ASCII names survive.
  return `=?UTF-8?B?${Buffer.from(subject, 'utf-8').toString('base64')}?=`
}

export interface DraftInput {
  to: string
  cc?: string // comma-separated CC recipients
  subject: string
  html: string
  attachments: Array<{ filename: string; content: Buffer }>
  sender?: string // mailbox to draft from/as (defaults to GMAIL_SENDER)
}

export interface DraftResult {
  draftId: string
  link: string
}

/** Create a Gmail draft (with the PDF attached) in the GMAIL_SENDER mailbox. */
export async function createGmailDraft(input: DraftInput): Promise<DraftResult> {
  const creds = loadCredentials()
  const sender = input.sender || process.env.GMAIL_SENDER
  if (!creds || !sender) {
    throw new Error('Gmail is not configured (set the service-account key and GMAIL_SENDER).')
  }

  const auth = new google.auth.JWT({
    email: creds.client_email,
    key: creds.private_key,
    scopes: SCOPES,
    subject: sender, // impersonate the shared mailbox (e.g. construction@wlth.com)
  })
  const gmail = google.gmail({ version: 'v1', auth })

  const boundary = 'wlg_' + b64url(String(input.to)).slice(0, 16)
  const parts = [
    `To: ${input.to}`,
    ...(input.cc ? [`Cc: ${input.cc}`] : []),
    `From: ${sender}`,
    `Subject: ${encodeSubject(input.subject)}`,
    'MIME-Version: 1.0',
    `Content-Type: multipart/mixed; boundary="${boundary}"`,
    '',
    `--${boundary}`,
    'Content-Type: text/html; charset="UTF-8"',
    'Content-Transfer-Encoding: base64',
    '',
    wrap76(Buffer.from(input.html, 'utf-8').toString('base64')),
  ]
  for (const att of input.attachments) {
    parts.push(
      `--${boundary}`,
      `Content-Type: application/pdf; name="${att.filename}"`,
      'Content-Transfer-Encoding: base64',
      `Content-Disposition: attachment; filename="${att.filename}"`,
      '',
      wrap76(att.content.toString('base64')),
    )
  }
  parts.push(`--${boundary}--`, '')
  const mime = parts.join('\r\n')

  const res = await gmail.users.drafts.create({
    userId: 'me',
    requestBody: { message: { raw: b64url(mime) } },
  })

  const draftId = res.data.id as string
  return { draftId, link: 'https://mail.google.com/mail/u/0/#drafts' }
}

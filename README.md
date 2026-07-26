# Welcome Letter Generator

Nuxt 4 + TypeScript app that automates the Customer Service welcome-letter
rebrand. The funder (Origin MMS) sends one Word doc per borrower; this tool
reads them, and the only thing typed by hand is the **BSB + account number**.

## Run

```bash
npm install
npm run dev      # http://localhost:3200
```

Requires **python3** on PATH (the letter engine is Python; called by the server).

## The workflow

1. **Upload Funder Docs** — pick a brand (WLTH / Mortgage Mart) and upload the
   funder’s `.docx` files (one per borrower; for an SMSF/Trust, the entity + each
   member together).
2. **BSB & Accounts** — the app parses the docs, auto-detects the loan type
   (Standard vs SMSF/Trust) and every party, and asks for the one manual field:
   the nominated direct-debit BSB + account (applied to all letters on the loan).
3. **Preview** — one branded letter per party (embedded PDF pages), plus an
   "Account linked to Offset?" answer that selects the email template.
4. **Save & Send** — enter each **member's** email (the entity gets no email),
   then **Create Draft Email** (a Gmail draft per member in hello@wlth.com, letter
   attached) and/or **Download All** (a ZIP of every party's PDF).

## Architecture

```
app/                      Nuxt front end (wizard, pages, components)
  composables/
    useLetterApi.ts       calls /api/letters/parse and /render (real);
                          drive/email/recent-letters still mocked
    useLetterWizard.ts    shared wizard state
server/
  api/letters/parse.post.ts    multipart .docx -> loan structure + parties
  api/letters/render.post.ts   multipart .docx + BSB/account -> merged letters
  utils/engine.ts              runs the Python engine, returns JSON
engine/                   the letter engine (Python 3)
  wlth_letter.py          parse a funder .docx -> data; render() -> letter text
  cli.py                  parse | render commands (called by the server)
  extract.py              docx text extraction helper
```

### The engine

`engine/cli.py` is the whole automation:

- **parse** — groups the uploaded funder docs into one loan, detects the SMSF/Trust
  structure (from the borrower/guarantor names), and returns the parties. The
  entity’s customer number becomes each member’s “Customer SMSF Number”.
- **render** — merges every party’s full letter, applying brand config (portal
  URL, phone, email, sign-off) and inserting the typed BSB/account.

Verified: it reproduces the three real Stevens finished letters **exactly**
(text-diff), including the SMSF fan-out and the members’ added SMSF-number line.

## Branded PDF

The **Download PDF** button on the Preview step generates a branded PDF that
reproduces the real letterhead — full-width brand banner, bordered 2-column
account tables, and the address footer. Both brands are supported:

- **WLTH** — grey band + blue "W" banner (`engine/assets/wlth/banner.png`).
- **Mortgage Mart** — dark band + "iMM" banner (`engine/assets/mma/banner.png`),
  MMA portal URL / phone / sign-off.

The repayment section is taken verbatim from the funder doc, so it renders
correctly for both Principal & Interest and Interest Only loans. Built with
**reportlab** (`engine/pdf_letter.py`) via `cli.py pdf <brand> <bsb> <account>
<partyIndex> <files...>`, served by `server/api/letters/pdf.post.ts`.
Install deps with `pip install -r engine/requirements.txt`.

## Download All (ZIP)

On **Save & Send**, **Download All** returns a ZIP of every party's branded PDF
(`engine/cli.py zip` → `server/api/letters/zip.post.ts`) — for a loan the user
files/uploads manually. (Google Drive upload was removed in favour of this.)

## Email drafts

On **Save & Send**, **Create Draft Email** generates each member's PDF and creates a Gmail
**draft** (letter attached, no send) in the shared `hello@wlth.com` inbox, with
the borrower as the recipient and an Offset/Standard body chosen from the "linked
to offset" answer (`server/utils/gmail.ts` + `emailTemplate.ts` →
`server/api/letters/email.post.ts`).

Two ways to configure it (Zapier takes priority when set):

**A) Zapier (simplest — no service account):** Create a Zap:
1. Trigger: **Webhooks by Zapier → Catch Hook** (copy the webhook URL).
2. Action: **Gmail → Create Draft**, connected to hello@wlth.com. Map
   To=`to`, Subject=`subject`, Body=`body`, Attachment=`attachment`.
3. In `.env`, set `ZAPIER_EMAIL_WEBHOOK_URL=<the Catch Hook URL>`. Restart.
The app POSTs `to`, `subject`, `body`, `filename`, `template` + the PDF file.

**B) Gmail service account** with domain-wide delegation for scope
`https://www.googleapis.com/auth/gmail.compose`; set `GMAIL_SENDER=hello@wlth.com`
(+ `GOOGLE_SERVICE_ACCOUNT_JSON`).

Until either is configured, the button reports "Email is not configured".

## What’s left to wire

- The dashboard **Recent Letters** table is still mock data (`getRecentLetters`
  in `useLetterApi.ts`) — wire it to a real store once letters are persisted.

Never commit funder docs or generated letters — they contain borrower PII.

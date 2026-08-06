# Letter history — Supabase setup

The dashboard's **Recent Letters** is backed by Supabase: a Postgres table holds
each letter's metadata and a private Storage bucket holds the PDF. All writes
happen server-side with the **service_role** key, so that secret never reaches
the browser.

You only need to do this once.

## 1. Create the table

Supabase dashboard → **SQL Editor** → run:

```sql
create table if not exists public.letters (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  letter_type text not null,
  type_label  text,
  brand       text,
  customer    text,
  reference   text,
  status      text,
  filename    text,
  pdf_path    text
);

create index if not exists letters_created_at_idx on public.letters (created_at desc);

-- Keep the table private. We use the service_role key server-side, which
-- bypasses RLS, so no policies are needed. Enabling RLS with no policies
-- blocks the anon/public key from ever reading it — which is what we want.
alter table public.letters enable row level security;
```

## 2. Create the Storage bucket

Dashboard → **Storage** → **New bucket**:

- Name: `letters`
- **Private** (leave "Public bucket" OFF) — downloads use short-lived signed URLs.

(Or via SQL:)

```sql
insert into storage.buckets (id, name, public)
values ('letters', 'letters', false)
on conflict (id) do nothing;
```

## 3. Set the environment variables

Dashboard → **Project Settings → API**. Copy:

- **Project URL** → `SUPABASE_URL`
- **service_role** secret → `SUPABASE_SERVICE_ROLE_KEY`

Set both **locally** (in `.env`) and in **Vercel → Project → Settings →
Environment Variables** (Production + Preview). `SUPABASE_URL` is already filled
in `.env`; paste the service_role key after `SUPABASE_SERVICE_ROLE_KEY=`.

Optional overrides (defaults shown): `SUPABASE_LETTERS_TABLE=letters`,
`SUPABASE_LETTERS_BUCKET=letters`.

Redeploy on Vercel after adding the variables.

## What gets saved, and when

| Action | Status recorded |
| --- | --- |
| Download a letter PDF (any type) | `Completed` |
| Create an email draft | `Draft` |
| Welcome "Download All" | one `Completed` row **per borrower** |

Blank template downloads (from the Templates page, no field values) are **not**
recorded. If a letter is both downloaded and emailed you'll get two rows — this
is intentional for now (an audit trail); we can de-duplicate later if you want.

If Supabase isn't configured, the app still works exactly as before —
persistence is skipped and Recent Letters shows an empty state.

# "Add to Google Drive" setup

The download pages have an **Add to Google Drive** button. When clicked, the user
signs in with their Google account, picks a destination folder, and the
letter PDFs upload straight into it.

It uses the least-privileged **`drive.file`** scope: the app can only create
files and write into the folder the user explicitly picks — it can never see the
rest of their Drive. This scope generally avoids Google's app-verification review.

You'll create two public values in Google Cloud (an OAuth client id and a browser
API key) and set them as `NUXT_PUBLIC_GOOGLE_*` env vars. They're **not secrets**
— they're embedded in the built app and are safe to expose.

## 1. Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and select
   (or create) a project. Note the **project number** (Dashboard → Project info) —
   that's the optional `APP_ID`.
2. **APIs & Services → Library** → enable **Google Picker API** and **Google Drive API**.

## 2. OAuth consent screen

**APIs & Services → OAuth consent screen**:
- User type: **Internal** (if everyone using the app is in your Google Workspace)
  — this needs no verification. Otherwise **External** and add testers.
- Fill in app name + support email.
- Scopes: you can leave the defaults; the app requests `drive.file` at runtime.

## 3. Credentials

**APIs & Services → Credentials → Create credentials**:

- **OAuth client ID** → Application type **Web application**.
  - **Authorized JavaScript origins** — add every origin the app runs on:
    - `http://localhost:3200` (local dev)
    - `https://wlth-internal-lettergen.vercel.app` (production)
    - any other preview/custom domains
  - (No redirect URI needed — the token flow is popup-based.)
  - Copy the **Client ID** → `NUXT_PUBLIC_GOOGLE_CLIENT_ID`.
- **API key** → copy it → `NUXT_PUBLIC_GOOGLE_API_KEY`.
  - Recommended: **restrict** it to the *Google Picker API* and to your
    HTTP referrers (the same origins as above).

## 4. Set the env vars

Local `.env`:

```
NUXT_PUBLIC_GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
NUXT_PUBLIC_GOOGLE_API_KEY=AIza...
NUXT_PUBLIC_GOOGLE_APP_ID=123456789012   # project number (optional)
```

Vercel → Project → Settings → **Environment Variables**: add the same three.

> ⚠️ These are read at **build time** for the static app, so set them in Vercel
> **before** redeploying, and restart `nuxt dev` locally after editing `.env`.

## How it behaves

- Until the client id + API key are set, the button is shown but disabled
  ("Google Drive isn't set up yet"). Nothing else is affected.
- On the Welcome flow it uploads one PDF per borrower; on form letters it
  uploads the single letter.
- Files upload to the folder the user picks (in their own Drive or a Shared
  Drive they can access).

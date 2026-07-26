# Deploying the Welcome Letter Generator

The app is **Node (Nuxt) + Python (the letter engine)**, packaged as one Docker
image (see `Dockerfile`). It runs on any container host — steps below use
**Render**, but Railway / Fly / a VM work the same way.

Access is gated by **Google sign-in restricted to @wlth.com**.

---

## 1. Create a Google OAuth client (one-time)

1. [console.cloud.google.com](https://console.cloud.google.com) → **APIs & Services → Credentials**.
2. **Create Credentials → OAuth client ID** → Application type **Web application**.
3. **Authorised redirect URIs** → add (you'll get the real domain in step 3, come back and fix this):
   ```
   https://YOUR-APP-DOMAIN/auth/google
   ```
4. Save the **Client ID** and **Client secret**.
5. (If prompted to configure the consent screen, set User type = **Internal** so
   it's limited to your Workspace.)

## 2. Put the code on GitHub

```bash
git init && git add -A && git commit -m "Welcome Letter Generator"
git branch -M main
git remote add origin https://github.com/YOUR-ORG/welcome-letter-generator.git
git push -u origin main
```
`.env` and secrets are git-ignored — they're set on the host instead (next step).

## 3. Deploy on Render

1. [render.com](https://render.com) → **New → Blueprint** → connect the repo.
   Render reads `render.yaml` and creates a Docker web service.
   (Or **New → Web Service → Docker** and point it at the repo.)
2. When it asks for the un-synced env vars, set:
   - `NUXT_OAUTH_GOOGLE_CLIENT_ID` — from step 1
   - `NUXT_OAUTH_GOOGLE_CLIENT_SECRET` — from step 1
   - `ZAPIER_EMAIL_WEBHOOK_URL` — your Zap's Catch Hook URL
   - (`NUXT_SESSION_PASSWORD` is auto-generated; `NUXT_ALLOWED_EMAIL_DOMAIN=wlth.com` is preset.)
3. Deploy. Render gives you a URL like `https://welcome-letter-generator.onrender.com`.
4. **Go back to the Google OAuth client** and set the redirect URI to
   `https://welcome-letter-generator.onrender.com/auth/google` (your real domain).

## 4. Try it

Visit the URL → you're sent to the login page → **Sign in with Google** with a
@wlth.com account → the app loads. Non-@wlth.com accounts are rejected.

---

## Environment variables (reference)

| Var | Purpose |
|---|---|
| `NUXT_SESSION_PASSWORD` | 32+ char secret sealing the login cookie (auto-generated on Render) |
| `NUXT_OAUTH_GOOGLE_CLIENT_ID` / `_SECRET` | Google OAuth client |
| `NUXT_ALLOWED_EMAIL_DOMAIN` | Allowed sign-in domain (`wlth.com`) |
| `ZAPIER_EMAIL_WEBHOOK_URL` | Zap Catch Hook for creating email drafts |

Python deps (`reportlab`, `pymupdf`) are installed into the image automatically
from `engine/requirements.txt` — nothing to configure.

## Run the image locally (optional)

```bash
docker build -t welcome-letters .
docker run -p 3000:3000 --env-file .env welcome-letters
# http://localhost:3000
```

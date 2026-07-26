# Deploying the Welcome Letter Generator

The app is **Node (Nuxt) + Python (the letter engine)**, packaged as one Docker
image (see `Dockerfile`). It runs on any container host — steps below use
**Render**, but Railway / Fly / a VM work the same way.

> ⚠️ **No login.** The app is publicly accessible to anyone with the URL and it
> handles borrower PII. Keep the URL private; put it behind a VPN / IP allowlist
> if you can, and treat the link as a secret.

---

## 1. Code is on GitHub

Already pushed to `afernandeswlth/Welcome_Letter` (branch `main`).
`.env` and secrets are git-ignored — they're set on the host instead.

## 2. Deploy on Render

1. [render.com](https://render.com) → **New → Blueprint** → connect the repo.
   Render reads `render.yaml` and builds the Docker web service.
   (Or **New → Web Service → Docker** pointed at the repo.)
2. Set the one env var when prompted:
   - `ZAPIER_EMAIL_WEBHOOK_URL` — your Zap's Catch Hook URL (for the email drafts)
3. Deploy. Render gives you a URL like `https://welcome-letter-generator.onrender.com`.

## 3. Use it

Open the URL → the app loads straight away (no sign-in) → upload funder docs,
generate, download the ZIP, create email drafts.

---

## Environment variables

| Var | Purpose |
|---|---|
| `ZAPIER_EMAIL_WEBHOOK_URL` | Zap Catch Hook for creating email drafts |

Python deps (`reportlab`, `pymupdf`) are installed into the image automatically
from `engine/requirements.txt` — nothing to configure.

## Run the image locally (optional)

```bash
docker build -t welcome-letters .
docker run -p 3000:3000 --env-file .env welcome-letters
# http://localhost:3000
```

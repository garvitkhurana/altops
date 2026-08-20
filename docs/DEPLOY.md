# Deploy Altline to altine.co (Render + Namecheap)

The app is a FastAPI server (`app.py`). Render hosts it and terminates HTTPS; Namecheap DNS points **altine.co** at Render.

## 1. Push to GitHub

Ensure the latest code is on GitHub (`garvitkhurana/altops` or your fork).

## 2. Create the Render service

1. Sign in at [render.com](https://render.com) (GitHub login is fine).
2. **New → Blueprint** → connect the repo → Render reads `render.yaml`.
3. Or **New → Web Service** manually:
   - **Build command:** `pip install -r requirements.txt && python3 credit_corpus.py`
   - **Start command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** Free (spins down after ~15 min idle; first request may take ~30s).

4. Under **Environment**, add any keys you want for live LLM runs (optional — deterministic demo works without them):
   - `NVIDIA_API_KEY`
   - `OPENROUTER_API_KEY`
   - `ANTHROPIC_API_KEY`

5. Deploy and wait until the service is **Live**. Note the default URL, e.g. `https://altine.onrender.com`.

## 3. Add custom domains in Render

In the service → **Settings → Custom Domains**:

1. Add `altine.co`
2. Add `www.altine.co`

Render shows the DNS records you need. Keep this tab open.

## 4. Configure Namecheap DNS

1. [Namecheap](https://www.namecheap.com) → **Domain List** → **altine.co** → **Manage** → **Advanced DNS**.
2. Remove any **AAAA** records (Render is IPv4-only).
3. Remove conflicting **A** / **CNAME** / **URL Redirect** records for `@` and `www` if they exist.

Add these records (TTL: **1 min** or **Automatic** while verifying):

| Type  | Host | Value |
|-------|------|-------|
| **A** | `@` | `216.24.57.1` |
| **CNAME** | `www` | `YOUR-SERVICE.onrender.com` |

Replace `YOUR-SERVICE.onrender.com` with the hostname Render gives you (same as the default `.onrender.com` URL, without `https://`).

Back in Render, click **Verify** next to each domain. SSL (Let's Encrypt) is issued automatically after DNS propagates (often 5–30 minutes).

Check propagation:

```bash
dig altine.co A +short
dig www.altine.co CNAME +short
```

## 5. Smoke test

- `https://altine.co/` — landing page
- `https://altine.co/demo` — interactive audit
- `https://altine.co/api/options` — JSON (should return facilities/providers)

## Notes

- **Free tier cold starts:** first visit after idle can be slow. Upgrade to a paid instance for always-on demos.
- **Demo without API keys:** the site works on the deterministic parser; "Run with model" needs env vars on Render.
- **LP demo:** `app_alts_lp.py` is not deployed by default; only `app.py` is the production entrypoint.

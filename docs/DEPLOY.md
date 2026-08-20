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

4. Set **`ALTLINE_PUBLIC=1`** in Environment (included in `render.yaml`). This serves a read-only sample audit at `/demo` — no LLM runs, no provider controls. Omit it locally to keep the full interactive demo.

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
- **Public site:** with `ALTLINE_PUBLIC=1`, visitors see a fixed sample audit only. Live model runs stay on your machine.
- **LP demo:** `app_alts_lp.py` is not deployed by default; only `app.py` is the production entrypoint.

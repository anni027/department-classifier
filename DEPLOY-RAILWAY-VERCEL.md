# Deploying split: backend on Railway, frontend on Vercel

The other deployment option. `DEPLOY.md` puts everything behind one Caddy on a
single Lightsail box; this one puts the API and the static site on two managed
platforms, each with its own TLS and its own public hostname.

```
                        browser
                           │
        ┌──────────────────┴───────────────────┐
        │                                      │
        ▼                                      ▼
  Vercel  <project>.vercel.app          Railway  <service>.up.railway.app
  Next.js frontend                      FastAPI backend  ──►  Postgres
        │                                      ▲
        └──── server components fetch ─────────┘
              over the public internet
```

**The one structural difference that drives everything below:** there is no
Caddy, so the frontend and the API are no longer on one origin. That single
change is why CORS becomes load-bearing, why the browser needs the API's URL
baked in at build time, and why three previously-automatic things had to be
moved into the repo's own config.

Use `DEPLOY.md` instead if you want one box, one bill and one origin. It is the
lower-effort option; this one buys managed TLS, no server patching, and separate
build pipelines, at the cost of the items in [What this gives
up](#what-this-gives-up) below.

---

## Before you start

- The repo pushed to GitHub (both platforms deploy from it, so the Railway
  login and the Vercel login need read access — this is what replaces
  `DEPLOY.md` step 5's deploy key).
- A Railway account and a Vercel account. **Railway has no free tier** — it
  gives a small trial credit and then bills by usage, so check current pricing
  before pointing a recruitment-week link at it.
- Nothing else. No domain is required for a first deploy; both platforms hand
  out a working HTTPS hostname for free.

---

## 1. Backend — Railway

### 1.1 Create the project and the database

1. **New Project** → **Deploy from GitHub repo** → pick this repository.
2. In that project, **Create** → **Database** → **Add PostgreSQL**.

### 1.2 Point the service at the backend directory

The repo has two apps in it, so Railway needs to know which one this service
builds. Open the backend service → **Settings** → **Source**:

| Setting | Value |
| ------- | ----- |
| Root Directory | `backend` |
| Branch | `main` (or whatever you deploy from) |

Setting the root directory does two things at once: it makes the build context
`backend/`, so `backend/Dockerfile`'s `COPY . .` copies the app and its data
files rather than the whole repository, and it makes Railway read
`backend/railway.json`, which is already committed and pins the builder, the
healthcheck and the restart policy. Nothing to configure by hand for those.

### 1.3 Variables

Service → **Variables** → **New Variable** → *Raw Editor* is fastest. Add all
four:

| Variable | Value | Why |
| -------- | ----- | --- |
| `ENV` | `production` | Disables `/docs` and turns on the fail-fast checks in `app/config.py`. |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Railway substitutes the Postgres service's own URL. **Type it exactly like this** — the name inside `${{ }}` has to match the database service's name (`Postgres` unless you renamed it). |
| `CORS_ORIGINS` | `https://<your-project>.vercel.app` | The frontend's origin. You will not know the exact value until step 2 — put a placeholder in now and come back, or do step 2 first. Comma-separate multiple origins with no spaces. |
| `DATA_DIR` | `app/data` | Already set by the Dockerfile; listing it here just makes it visible/overridable. |


`DATABASE_URL` arrives from Postgres as a bare `postgresql://…` URL.
`backend/app/config.py` rewrites that to `postgresql+psycopg://…` on load,
because SQLAlchemy otherwise reads it as **psycopg2**, a driver this project
does not install — the failure is a `ModuleNotFoundError` raised at import that
never mentions the connection string. Do not "fix" this by pasting a
hand-edited URL into the variable; the rewrite exists so the provider's own
variable works as-is.

`PORT` is deliberately **not** in this table. Railway injects it, and
`backend/Dockerfile`'s `CMD` is written to bind whatever `PORT` says
(defaulting to 8000 for Lightsail).

### 1.4 Give it a public hostname

Service → **Settings** → **Networking** → **Public Networking** → **Generate
Domain**. You get something like
`department-classifier-production.up.railway.app`.

Keep that hostname — it is the frontend's API URL in step 2. If you add a
custom domain later (`api.yourdomain.com`), note that changing it means the
frontend has to be **rebuilt**, not just reconfigured — see step 3.

### 1.5 Verify the backend on its own

```bash
curl -s https://<railway-domain>/api/v1/health
# {"status":"ok","departments_loaded":15,"questions_loaded":55}
```

Do this *before* touching Vercel. If this does not return `ok`, nothing
downstream will work and the failure will look like a frontend bug. The most
common cause at this stage is a variable reference that did not resolve —
Railway's deploy log shows the app refusing to start with
`ENV=production requires DATABASE_URL to be set explicitly`.

---

## 2. Frontend — Vercel

1. **Add New…** → **Project** → import the same repository.
2. **Root Directory** → **Edit** → `frontend`. (Vercel shows the framework
   preset as Next.js once this is set — leave the build and output settings
   alone.)
3. **Environment Variables** — add one:

| Variable | Value |
| -------- | ----- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://<railway-domain>/api/v1` |

Three things about that value:

- **The `/api/v1` suffix is required.** The API's routes all live under that
  prefix; leaving it off produces 404s on every call.
- **No trailing slash.** It is concatenated with paths like
  `/classification/start`, and a trailing slash yields `//api/v1` in some
  fetch paths.
- **It is compiled in at build time.** The name starts with `NEXT_PUBLIC_`, so
  Next inlines the literal string into the browser bundle. Changing it in the
  dashboard does nothing until the project is **redeployed**, which is exactly
  the trap `DEPLOY.md` documents for the Docker build.

4. **Do not set `INTERNAL_API_BASE_URL`.** That variable exists on Lightsail
   because server components there would otherwise have to loop out through the
   public domain and depend on hairpin NAT. On Vercel there is no such problem:
   the server-side fetch simply goes out to the Railway hostname over the
   public internet, which is what `lib/api.ts` falls back to when the variable
   is unset.
5. **Deploy.**

---

## 3. Close the loop

The frontend needs the backend's URL (done in step 2) and the backend needs the
frontend's origin. Take the domain Vercel just gave you — the **production**
one, `https://<project>.vercel.app`, not a preview URL — and put it in
Railway's `CORS_ORIGINS`, then let Railway restart the service.

Then verify end to end:

1. Open the Vercel URL and take the quiz. Questions loading proves the API is
   reachable; submitting an answer proves CORS is right.
2. Visit `/departments` and a department page. Those are server components
   (`export const dynamic = "force-dynamic"`), so they exercise the
   server-to-server path rather than the browser path — they can fail
   independently of the quiz.

---

## Custom domains (optional)

| Hostname | Platform | Where |
| -------- | -------- | ----- |
| `api.yourdomain.com` | Railway | Service → Settings → Networking → **Custom Domain** |
| `app.yourdomain.com` | Vercel | Project → Settings → Domains |

Then update both sides, in this order:

1. `CORS_ORIGINS` on Railway → `https://app.yourdomain.com`
2. `NEXT_PUBLIC_API_BASE_URL` on Vercel → `https://api.yourdomain.com/api/v1`
3. **Redeploy the frontend.** See step 2 — this variable is baked in, so a
   domain change without a rebuild leaves the browser calling the old hostname.

Keep both `*.vercel.app` and `*.railway.app` entries out of `CORS_ORIGINS` once
custom domains are live, unless you actually use them.

---

## What this gives up

Everything here was previously handled by Caddy, and Caddy is not in the
picture for this deployment. `Caddyfile`, `docker-compose.prod.yml` and
`deploy.sh` are all unused by it — they still work for `DEPLOY.md`.

| Lost | Consequence | Status |
| ---- | ----------- | ------ |
| `X-Real-IP` set by `header_up` | The rate limiter has no trustworthy client address | **Handled.** `app/api/ratelimit.py` now falls back to Railway's `X-Forwarded-For`, whose leftmost entry Railway documents as the real client. This is what stops every student sharing one bucket — see the caveat below. |
| Security headers | No HSTS, CSP, `nosniff`, `X-Frame-Options` | **Mostly handled.** `frontend/next.config.mjs` now sets all of them except CSP. |
| CSP | No defense-in-depth against injected script | **Not reproduced.** The Caddyfile's `connect-src 'self'` is only correct on one origin; copying it to Vercel would block the quiz outright. Doing it properly means interpolating `NEXT_PUBLIC_API_BASE_URL` into the directive. |
| 8 KB request body cap | FastAPI accepts arbitrarily large bodies on the write endpoints | **Open.** The largest legitimate body is ~120 B, so this is a cheap DoS lever against a session endpoint. Re-establishing it needs a proxy or middleware. |
| One origin | CORS is now load-bearing instead of cosmetic | Inherent. A wrong `CORS_ORIGINS` is a broken site, not a degraded one. |

Two more operational notes:

- **Do not scale the backend past one replica.** `app/db/cleanup.py` runs the
  session reaper in-process and its docstring assumes "exactly one backend
  container". A second replica would run a second reaper — harmless (the two
  delete the same rows) but no longer the deliberate single runner.
- **Back up Postgres yourself.** Railway's automated backups are a paid
  feature. The `pg_dump` recipe in `DEPLOY.md` works unchanged; just point the
  connection string at the public URL instead of a container.

### The rate-limiter caveat, stated plainly

On Lightsail the limiter is safe because Caddy *overwrites* `X-Real-IP`, and
`backend/tests/test_rate_limit.py` exists to document that dependency.

On Railway the equivalent guarantee is Railway's, not ours: their edge owns
`X-Forwarded-For` and the leftmost entry is the real client. If Railway ever
stops stripping a client-supplied value there, an attacker could rotate the
leftmost entry and mint fresh rate-limit buckets. Worth re-reading
`app/api/ratelimit.py` before any recruitment window; it is the one control
bounding how much an anonymous caller can write to the database.

---

## Troubleshooting

**Deploy fails immediately with `ModuleNotFoundError: No module named 'psycopg2'`.**
`DATABASE_URL` was not the bare `postgresql://` form the rewrite in
`app/config.py` expects — most likely a URL pasted with a scheme it does not
recognise.

**The app exits at startup with `ENV=production requires DATABASE_URL to be set explicitly`.**
The `${{Postgres.DATABASE_URL}}` reference did not resolve. Check the service
name inside the braces matches the Postgres service exactly, and that both
services are in the same environment.

**The app exits with `ENV=production requires CORS_ORIGINS to be set explicitly` or refuses `*`.**
Both checks are in `app/config.py` and both are intentional. Set a real origin.

**Questions load but submitting an answer fails, with a CORS error in the console.**
`CORS_ORIGINS` on Railway does not match the origin the browser is on. Origin
comparison is exact: `https://` counts, a trailing slash does not match, and
preview deployments get a *different* hostname per branch
(`<project>-git-<branch>-<team>.vercel.app`) — each one needs its own entry if
you want to test previews.

**Every API call 404s.**
`NEXT_PUBLIC_API_BASE_URL` is missing the `/api/v1` suffix, or still points at
the placeholder from before the Railway domain existed. Remember: fix it, then
redeploy — a rebuild is what makes it take effect.

**`/departments` pages 500 while the quiz works.**
These are server components, so they fail independently of the browser path.
Check the Vercel function logs for the fetch error; the API URL is inlined the
same way, so a wrong value breaks both, but a network or DNS failure breaks
only these.

**Railway marks the deploy unhealthy.**
`backend/railway.json` asks for `/api/v1/health`, which reports whether the
department and question files actually loaded. A 503 there means the data files
are missing from the image — most likely the service's Root Directory is the
repo root rather than `backend` (step 1.2), so `COPY . .` never picked up
`app/data/`.

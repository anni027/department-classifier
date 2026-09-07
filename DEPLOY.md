# Deploying on AWS Lightsail

One Lightsail instance runs the whole stack with Docker Compose: Postgres, the
FastAPI backend, the Next.js frontend, and Caddy in front terminating TLS.

```
                    :80 / :443
  internet ──────────► Caddy ──┬── /api/*  ──► backend  :8000 ──► postgres :5432
                               └── /*       ──► frontend :3000
```

Caddy puts both services on **one origin**, so the browser never makes a
cross-origin request and TLS certificates are issued and renewed automatically.

---

## Before you start

- An AWS account with Lightsail access.
- A domain (or subdomain) you can point at an IP address. **TLS will not work
  without one** — Let's Encrypt does not issue certificates for bare IPs. If
  you have no domain yet, see [Running without a domain](#running-without-a-domain).
- Push access to `taqneeq/Department_Classifier_19.0`, which is **private** —
  the server needs credentials to clone it (step 5).

---

## 1. Create the instance

Lightsail console → **Create instance**:

| Setting  | Value |
| -------- | ----- |
| Region   | Mumbai (`ap-south-1`) if your students are in India — it is the closest region and the latency difference is noticeable |
| Platform | Linux/Unix |
| Blueprint| **OS Only → Ubuntu 22.04 LTS** (not the "Node.js" or "Django" blueprint) |
| Plan     | **2 GB RAM minimum** |

**The 2 GB plan matters.** `next build` runs on this machine and needs roughly
1.5–2 GB. On a 512 MB or 1 GB instance the build is killed by the OOM reaper
partway through, usually with a misleading "exit code 137". If you must use a
1 GB plan, add swap first:

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Check current plan pricing in the console — the tiers change.

## 2. Attach a static IP

Lightsail → **Networking** → **Create static IP** → attach it to the instance.

Do this *before* pointing DNS. An instance's default public IP changes if it is
ever stopped and started, which would break both DNS and the certificate.
A static IP is free while it stays attached.

## 3. Open the firewall

Lightsail → instance → **Networking** → **IPv4 Firewall**. Add:

| Application | Protocol | Port |
| ----------- | -------- | ---- |
| HTTP        | TCP      | 80   |
| HTTPS       | TCP      | 443  |

**Port 80 is not optional.** Let's Encrypt validates over HTTP before issuing
the certificate; with only 443 open, certificate issuance fails and the site
never comes up on HTTPS.

Leave the database port closed — Postgres is only reachable inside the Docker
network and is deliberately not published to the host.

## 4. Point DNS at the static IP

Create an `A` record for your domain pointing at the static IP, then confirm it
has propagated **before deploying**:

```bash
dig +short classifier.taqneeq.example
```

If this does not print your static IP, wait. Deploying early means Caddy
requests a certificate for a name that does not resolve to it, gets refused,
and then backs off — the retry can take a while.

## 5. Install Docker and clone

SSH in (the browser-based client in the Lightsail console works fine):

```bash
sudo apt-get update && sudo apt-get upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker            # or log out and back in
docker compose version   # should print v2.x
```

The repo is private, so clone with a token or a deploy key:

```bash
# Option A — GitHub CLI (simplest)
sudo apt-get install -y gh && gh auth login
gh repo clone taqneeq/Department_Classifier_19.0 && cd Department_Classifier_19.0

# Option B — read-only deploy key (better for a shared server)
ssh-keygen -t ed25519 -C "lightsail-deploy" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# Add that key at: repo → Settings → Deploy keys → Add deploy key (read access)
git clone git@github.com:taqneeq/Department_Classifier_19.0.git
cd Department_Classifier_19.0
```

## 6. Configure

```bash
cp .env.production.example .env.production
openssl rand -base64 24        # use this for POSTGRES_PASSWORD
nano .env.production
```

Set `DOMAIN` to your real domain and `POSTGRES_PASSWORD` to the generated
value. `DOMAIN` drives three things at once — the certificate Caddy requests,
the CORS origin the backend accepts, and the API URL compiled into the frontend
bundle — so it must be exactly the hostname users will visit, with no scheme
and no trailing slash.

`.env.production` is gitignored. Keep the password somewhere safe; it is not
recoverable from the running container.

## 7. Deploy

```bash
./deploy.sh
```

The script checks its prerequisites, pulls the latest commit, builds both
images, starts the stack, then polls the API's own health endpoint until it
reports ready. First run takes several minutes — mostly `next build`.

Flags: `--no-pull` (deploy the working tree), `--no-build` (restart without
rebuilding), `--logs` (follow logs afterwards).

## 8. Verify

```bash
curl -s https://YOUR_DOMAIN/api/v1/health
# {"status":"ok","departments_loaded":15,"questions_loaded":55}
```

Then open `https://YOUR_DOMAIN` and take the quiz end to end. If the questions
load but submitting an answer fails, that is almost always the API URL —
see troubleshooting below.

---

## Updating after a code change

```bash
cd Department_Classifier_19.0 && ./deploy.sh
```

Postgres keeps running and its volume is untouched, so in-flight sessions
survive. There is no migration step: the backend creates its single `sessions`
table at startup if it is missing.

## Everyday operations

```bash
compose() { docker compose --env-file .env.production -f docker-compose.prod.yml "$@"; }

compose ps                     # what is running
compose logs -f backend        # follow API logs
compose restart backend        # restart one service
compose down                   # stop everything (data volume survives)
```

### Back up the database

```bash
compose exec -T postgres pg_dump -U taqneeq taqneeq | gzip > backup-$(date +%F).sql.gz
```

Restore:

```bash
gunzip -c backup-2026-09-08.sql.gz | compose exec -T postgres psql -U taqneeq -d taqneeq
```

Sessions are quiz answers rather than anything sensitive, but they are still
student data — keep backups off the instance and know which region they sit in.

---

## Troubleshooting

**The frontend loads but every API call fails.**
`NEXT_PUBLIC_API_BASE_URL` is compiled into the JavaScript bundle at build
time, not read at runtime. Editing `DOMAIN` and restarting will not change it.
Rebuild:

```bash
./deploy.sh          # rebuilds with the current DOMAIN
```

To confirm what a built image actually contains:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  run --rm --entrypoint sh frontend -c "grep -rlo 'YOUR_DOMAIN' .next/static | head"
```

**The build dies with exit code 137.** Out of memory during `next build`. Use a
2 GB instance or add swap (step 1).

**No certificate / browser warning.** Check `compose logs caddy`. Usual causes,
in order: port 80 closed in the Lightsail firewall, DNS not yet resolving to
the static IP, or `DOMAIN` not matching the hostname you are visiting.

**`FATAL: password authentication failed`.** The Postgres volume was created
with a different password and kept it. Either restore the original password in
`.env.production`, or wipe the volume — **this deletes all sessions**:

```bash
compose down -v && ./deploy.sh
```

**The API is healthy but pages 500.** The `/departments` pages are server
components, so Next fetches the API from *inside* the container through the
public URL. That works, but it means the instance must be able to reach its own
domain. If DNS inside the container is broken, those pages fail while the quiz
still works.

---

## Running without a domain

For a quick internal demo, put the static IP in `DOMAIN` and change the
Caddyfile's site line to `:80` so Caddy serves plain HTTP:

```
:80 {
	handle /api/* { reverse_proxy backend:8000 }
	handle { reverse_proxy frontend:3000 }
}
```

Then set `NEXT_PUBLIC_API_BASE_URL` to `http://STATIC_IP/api/v1` in
`docker-compose.prod.yml` and `CORS_ORIGINS` to `http://STATIC_IP`. This is
fine for a demo and not fine for real students — the quiz would travel
unencrypted.

---

## Notes and known rough edges

- **Builds happen on the production instance.** Simple, but a build failure and
  a deploy failure look alike, and the build competes for RAM with the running
  site. If this becomes a problem, build in GitHub Actions, push to a registry,
  and have `deploy.sh` pull images instead.
- **`requirements.txt` includes `pytest` and `httpx`**, so they end up in the
  backend image. Harmless, roughly a few MB; splitting dev dependencies out
  would trim it.
- **One instance is a single point of failure.** For a recruitment window that
  is a reasonable trade; just take a backup before the link goes out.
- **Accuracy caveat**, unrelated to hosting: the classifier picks the right
  department around 85% of the time, and the correct one is in the top three
  essentially always. See `CLASSIFIER_SPEC.md`.

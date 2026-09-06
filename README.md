# Taqneeq Department Classifier

Adaptive questionnaire that recommends which Taqneeq festival department a student
best fits, from a deterministic trait-scoring pipeline (no RAG/embeddings/entropy).

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (for Postgres via `docker compose`)

## Project architecture

```
Frontend (Next.js)  ->  REST API (FastAPI)  ->  Session repository (Postgres)
                                              ->  Classification engine (pure Python, core/)
```

`backend/app/core/` (models, scoring, classifier, data_loader) has zero FastAPI/DB
imports — it's plain functions/dataclasses over `departments.json` / `questions.json`,
independently unit-tested. `backend/app/api/` wires HTTP to it; `backend/app/db/`
is the only place SQL lives.

## Classification algorithm

1. Every session asks 4 fixed **seed questions** (`q01`-`q04`, an explicit constant
   in `core/classifier.py` — never derived from array position).
2. Every trait starts at `0.5`. Each 1-5 answer normalizes to `(value-1)/4`.
3. Trait update: primary trait `new = old*0.6 + normalized*0.4`; each secondary
   trait uses half that learning rate (`new = old*0.8 + normalized*0.2`).
4. `department_score = sum(trait_score * department_weight)` over all 15 traits
   (a plain dot product — no cosine similarity, no normalization, per spec).
5. Scores -> probabilities via a numerically-stable softmax.
6. After each answer (once 8+ have been answered), stop if `top_prob >= 0.65`
   AND `top_prob - second_prob >= 0.15`. Always stop at 12 questions.
7. Adaptive question selection (after the 4 seeds) scores every unanswered
   question: `+3 * top1_dept.weight[trait]` (continuous, not a threshold),
   `+2 * top2_dept.weight[trait]`, `+3` if the trait is untested so far, `+2`
   if the question's `distinguishes` list covers both leading departments,
   plus a `0-0.05` jitter to break exact ties only.
8. The final explanation (what you'll do / skills gained / strongest traits)
   is generated deterministically from the department's `description` string
   and the user's trait scores — `departments.json` has no separate
   responsibilities/skills fields, so nothing is invented there; the raw data
   files are never modified.

A known, inherent property of this exact (unnormalized) formula: departments
whose weight vector is high across *many* traits (e.g. Workshops, Marketing)
have a structural head start over narrow specialists, since every trait
starts at a neutral 0.5. See `backend/scripts/personas.py` output for how
this plays out across ten synthetic personas — most still land somewhere
sensible, but it's worth knowing about if a result looks surprising.

## Installation

```bash
git clone <repo>
cd "Taqneeq Dept Classifier 19.0"
docker compose up -d          # starts Postgres on localhost:5434
cd backend
python -m venv .venv && .venv\Scripts\activate   # (or source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
cd ../frontend
npm install
```

## Environment variables

Copy the example files and adjust if needed:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

- `DATABASE_URL` - Postgres connection string. The bundled `docker-compose.yml`
  maps Postgres to host port **5434** (not 5432) to avoid clashing with any
  Postgres already installed locally — keep this in sync if you change it.
- `CORS_ORIGINS` - comma-separated list of allowed frontend origins.
- `NEXT_PUBLIC_API_BASE_URL` - where the frontend finds the backend API.

## Database setup

`docker compose up -d` starts Postgres. The backend creates its one `sessions`
table automatically on startup (`metadata.create_all`) — no separate
migration step for this schema.

## Backend startup

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Frontend startup

```bash
cd frontend
npm run dev
```

App: http://localhost:3000

## Testing

```bash
cd backend
pytest                          # 54 tests: scoring, seed order, adaptive
                                 # selection, stopping rule, full-session
                                 # simulation, data integrity, API contract
python -m scripts.personas      # synthetic-persona sanity check (prints
                                 # results for 10 personas; a few loose
                                 # asserts on the unambiguous ones)
```

Frontend:

```bash
cd frontend
npx tsc --noEmit    # type-check
npm run build       # production build
```

## Known dependency advisory

`npm audit` reports one high-severity advisory in a **transitive** `postcss`
copy bundled inside `next`'s own internals (not the project's direct
`postcss` dependency, which is pinned to a patched version). Fixing it
requires jumping to Next.js 16 (a breaking major-version change) — left as a
deliberate follow-up rather than an unreviewed major bump.

## API overview

All endpoints are under `/api/v1`:

- `POST /classification/start`
- `POST /classification/answer`
- `GET /classification/status/{session_id}`
- `GET /departments`, `GET /departments/{id}`, `GET /departments/{id}/similar`
- `GET /health`

Full request/response schemas are in the auto-generated Swagger UI (`/docs`).

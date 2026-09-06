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
2. Every trait has a prior of `0.5`. Each 1-5 answer normalizes to `(value-1)/4`.
3. Trait score: the weighted mean of the `0.5` prior (weight `0.6`) and every
   normalized answer that touched the trait (weight `1.0` as that answer's
   primary trait, `0.5` as a secondary). Untouched traits stay at `0.5`; there
   is no learning rate, so answer order doesn't matter.
4. `department_score` = cosine similarity between the **mean-centred** trait
   vector and the **mean-centred** department weight vector, over all 15 traits.
   Centring compares profile *shape* rather than magnitude, so a department with
   broadly high weights gets no head start. If either centred vector is all
   zeros — a flat profile, i.e. session start or a student who answers `3` to
   everything — the score is `0.0` for every department, which is the honest
   "no signal yet" answer and yields a uniform `1/15` at step 5.
5. Scores -> probabilities via a numerically-stable softmax at
   `TEMPERATURE = 0.05` (`core/scoring.py`). This is the tuning knob: lower
   sharpens confidence and stops the quiz sooner, higher flattens it and asks
   more questions.
6. After each answer (once 14+ have been answered), stop if `top_prob >= 0.65`
   AND `top_prob - second_prob >= 0.15`. Always stop at 15 questions — a
   product ceiling on how long students will stay engaged, not a measured
   optimum. The minimum is set by measured accuracy: at the old 8/12 the right
   department came out on top for only 73% of profile-matched students, because
   confidence crosses the threshold while most traits are still at the prior.
   See `CLASSIFIER_SPEC.md` for the accuracy figures and for why adding
   questions on low-variance traits makes results worse at this cap.
7. Adaptive question selection (after the 4 seeds) scores every unanswered
   question: `+3 * top1_dept.weight[trait]` (continuous, not a threshold),
   `+2 * top2_dept.weight[trait]`, `+3` if the trait is untested so far, `+2`
   if the question's `distinguishes` list covers both leading departments,
   plus a `0-0.05` jitter to break exact ties only.
8. The final explanation is deterministic. "What you'll do" and "skills
   gained" are the department's own `responsibilities` and `skills` from
   `departments.json` (the Taqneeq Department Guide content), returned
   verbatim — nothing is paraphrased or invented. Only "strongest traits"
   depends on the student, ranked by `trait_score * department_weight`.

Cosine similarity is used for classification (step 4) and, separately, by
`GET /departments/{id}/similar`. The two are not the same computation: the
browsing endpoint compares *raw, uncentred* department weight vectors and is
unaffected by the classification rules above. See `CLASSIFIER_SPEC.md` for the
measurements that motivated the current scoring rules.

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

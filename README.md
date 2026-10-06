# LegalMind — Phase 5 Working / Cumulative

LegalMind is a legal document intelligence platform focused on **Indian Supreme Court judgments**.

## Included phases

- **Phase 1:** PDF ingestion, page-aware extraction, legal entities, sections, chunks, PostgreSQL + pgvector.
- **Phase 2:** BM25 + semantic + hybrid RRF retrieval, filters, reranking and retrieval logging.
- **Phase 3:** Ask LegalMind RAG, query classification, provider abstraction, citations, evidence coverage/confidence, uncertainty handling and RAG logging.
- **Phase 4:** Similar cases, issue extraction, timelines, case comparison and versioned legal-transformer NER.
- **Phase 5:** Evaluation, analytics, security hardening, RQ/Redis worker, CI regression tests and Docker deployment.

## Recommended deployment

1. Copy `.env.example` to `.env`.
2. Change `ADMIN_API_KEY`, `EVALUATOR_API_KEY` and `AUTH_SECRET` to strong random values.
3. Add a real `LLM_API_KEY` for the configured provider if you want Ask LegalMind to use live model calls.
3. Start the complete stack:

```powershell
docker compose up --build
```

The backend automatically runs Alembic migrations on startup.

Open:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

The Analytics and Evaluation pages use a runtime login and an HttpOnly session cookie. API keys are not embedded in the frontend bundle or stored in browser storage. CLI/API clients may still use `X-API-Key`.

## Local development without Docker

### PostgreSQL

Use a PostgreSQL instance with the `vector` extension, then set `DATABASE_URL` in `backend/.env`.

### Backend

```powershell
cd backend
copy .env.example .env
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

For local development without Redis, set:

```env
USE_WORKER=false
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Phase 5 evaluation

Held-out cases live in:

`backend/tests/evaluation/heldout.json`

The file is intentionally a **starter benchmark**. Replace the empty `relevant_ids` with labeled chunk/document IDs before using the retrieval metrics as a meaningful quality gate.

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Protected evaluator endpoints:
- `POST /api/v1/evaluation/run`
- `GET /api/v1/evaluation/results`
- `GET /api/v1/evaluation/export`
- `GET /api/v1/analytics`

Use the `X-API-Key` header with the evaluator key.

## Backup

Linux/macOS:

```bash
./backend/scripts/backup_postgres.sh
```

## Security notes

- Uploads must have a PDF extension/content type and `%PDF-` magic bytes.
- Upload size is limited by `MAX_UPLOAD_MB`.
- API requests are rate limited.
- Admin/evaluator endpoints require a server-side session cookie or API key.
- The frontend never receives or stores the raw evaluator/admin key after login.
- Uploaded documents can be deleted with cascading chunks and embeddings.
- Retention cleanup is available through the admin endpoint when `RETENTION_DAYS > 0`.
- Never commit `.env` or real API keys.

## Known scope decisions

- Jurisdiction: India — Supreme Court judgments.
- OCR: disabled; scanned PDFs are detected rather than OCR'd.
- LLM: `openai-compatible` is the default; configure `LLM_API_KEY` for live calls. Tests can instantiate the deterministic mock provider directly.
- Embeddings: `sentence-transformers/all-mpnet-base-v2` by default, with the 768-dimensional `sentence-transformers/all-distilroberta-v1` fallback. Both match the pgvector column dimension.
- Worker: RQ + Redis.

## Evidence status

The evaluation framework is complete, but the repository does **not fabricate legal relevance labels**. The included held-out file is a starter schema. See `benchmark/README.md` and `MANUAL_QA_CHECKLIST.md` for the collection and QA workflow.

## Remaining production work

The system is runnable, but before treating it as a production legal research system you should still:
1. Build a real labeled retrieval/QA benchmark with human judgments.
2. Replace heuristic faithfulness/relevance metrics with human or model-assisted evaluation.
3. Decide whether scanned-PDF OCR is required and add a trusted OCR pipeline if needed.
4. Replace API-key auth with your organization's SSO/JWT/RBAC if multiple real users are expected.
5. Put secrets in a managed secret store in production.
6. Test backup restoration, retention jobs and disaster recovery.
7. Run the full Docker stack in a Docker-enabled environment and perform load/security testing.
8. Pin/lock frontend dependencies with a committed lockfile for reproducible builds.

## Windows local mode (no Docker)

If Docker/WSL is unavailable, use `LOCAL_RUN.md`. This mode uses native PostgreSQL + pgvector and disables Redis/RQ for local development.

Quick start:
1. Install Python 3.11/3.12, Node.js 20+, PostgreSQL 16+ with pgvector.
2. Run `check_local_prereqs.bat`.
3. Run `setup_local.bat`.
4. Create the `legalmind` PostgreSQL database and enable `vector` (see `LOCAL_RUN.md`).
5. Run `migrate_local.bat`.
6. Run `run_all_local.bat`.


# LegalMind Phase 5 — Evaluation, Analytics, Hardening and Deployment

This ZIP is cumulative: Phases 1–4 remain intact and Phase 5 adds measurable evaluation, analytics, security hardening, worker processing and deployment.

## Decisions
- Jurisdiction: India — Supreme Court judgments.
- OCR: not supported; scanned PDFs are detected and surfaced for OCR in a future phase.
- Auth: API-key roles for evaluator/admin endpoints. Regular research endpoints remain open for local/dev use.
- LLM: provider remains swappable; default mock provider keeps local setup usable.
- Embeddings: `ahb-sjsu/lebse`, 768 dimensions; changing it requires re-indexing.
- Worker: RQ + Redis enabled by default in Docker.

## New APIs
- `GET /api/v1/analytics`
- `GET /api/v1/metrics`
- `POST /api/v1/evaluation/run`
- `GET /api/v1/evaluation/results`
- `GET /api/v1/evaluation/export?fmt=json|csv`
- `POST /api/v1/admin/retention`

## Security
- PDF magic-byte validation
- in-process rate limiting
- API-key role protection for admin/evaluator endpoints
- real deletion cascades chunks and embeddings via FK constraints
- retention cleanup removes DB rows and stored PDFs
- prompt-injection tests retained from Phase 3

## Deployment
`docker compose up --build` starts Postgres/pgvector, Redis, backend, worker and frontend. Backend runs Alembic migrations on startup.

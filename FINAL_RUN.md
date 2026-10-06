# LegalMind Phase 5 — Final No-Docker Run

This package includes the final local fixes:
- local API standardized on port 8001
- local embedding default uses `sentence-transformers/all-mpnet-base-v2` (768 dimensions)
- embedding loader has a safe configurable fallback
- analytics separates obvious QA/fixture artifacts from production metrics
- production frontend uses a lightweight esbuild bundle instead of the stalled Vite production transform
- Vite remains available for development

## First time
1. Install Python 3.11+, Node 20+, PostgreSQL 16+ with pgvector.
2. Create the `legalmind` database and enable the `vector` extension.
3. Run `setup_local.bat`.
4. Run `migrate_local.bat`.

## Run development mode
Run:
`run_all_local.bat`

Frontend: http://127.0.0.1:5173
Backend: http://127.0.0.1:8001
API docs: http://127.0.0.1:8001/docs

## Run production frontend
Run:
`run_production_local.bat`

This creates `frontend/dist` with esbuild and starts Vite preview on port 5173.

## Important
The ZIP does not contain your PostgreSQL database or downloaded ML model caches. Those remain local machine resources.

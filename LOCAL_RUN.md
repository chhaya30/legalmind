# LegalMind Phase 5 — Windows Local Run (No Docker)

This version runs without Docker. It uses native Windows PostgreSQL and runs document processing inside the FastAPI process using background tasks. Redis/RQ is disabled for local mode.

## Required software

1. Python 3.11 or 3.12
2. Node.js 20+
3. PostgreSQL 16+ with the **pgvector extension installed**
4. A browser

Docker, Redis and WSL are **not required** for local mode.

## 1. PostgreSQL

Create a database user and database. Open `psql` as a PostgreSQL administrator and run:

```sql
CREATE USER legalmind WITH PASSWORD 'legalmind';
CREATE DATABASE legalmind OWNER legalmind;
```

Connect to the new database and enable pgvector:

```sql
\c legalmind
CREATE EXTENSION IF NOT EXISTS vector;
```

If `CREATE EXTENSION vector` fails, your PostgreSQL installation does not have pgvector installed. Install a Windows build of pgvector compatible with your PostgreSQL version before continuing.

If you already use a PostgreSQL user/database, edit `backend/.env` and change `DATABASE_URL` accordingly.

## 2. Setup

From this folder run:

```powershell
.check_local_prereqs.bat
.setup_local.bat
```

The setup creates `backend\.venv`, installs Python dependencies, creates `backend\.env`, and installs frontend dependencies.

The first Python install is large because LegalMind uses PyTorch, Sentence Transformers and the legal NER model.

## 3. Migrate database

```powershell
.migrate_local.bat
```

## 4. Start the application

Use:

```powershell
.run_all_local.bat
```

or start separately:

```powershell
.run_backend_local.bat
.run_frontend_local.bat
```

Open:

- Frontend: http://127.0.0.1:5173
- API: http://127.0.0.1:8001
- Swagger: http://127.0.0.1:8001/docs

## 5. Local credentials

The generated local environment uses:

- Admin key: `legalmind-admin-123`
- Evaluator key: `legalmind-evaluator-123`

Change these before sharing the application with anyone.

## 6. LLM behavior

Local mode starts with `LLM_PROVIDER=mock`, so Ask LegalMind works without an API key. For real LLM calls, edit `backend/.env`:

```env
LLM_PROVIDER=openai-compatible
LLM_API_KEY=your_key
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

Then restart the backend.

## 7. Redis/RQ

Local mode uses:

```env
USE_WORKER=false
```

so Redis is not required. Upload processing uses FastAPI background tasks. Docker/production mode can continue to use RQ + Redis.

## 8. First test

1. Open the frontend.
2. Upload `backend/tests/fixtures/sample_judgment.pdf`.
3. Wait for `ready`.
4. Open the document.
5. Test Search, Ask, Issues, Timeline and Similar Cases.
6. Upload a second judgment and test Compare.
7. Try an absent-topic question to verify insufficient evidence.

## 9. Useful commands

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend build:

```powershell
cd frontend
npm run build
```

## Known limitation

This is the **no-Docker developer/local mode**. It intentionally keeps the full PostgreSQL + pgvector data model, but disables the Redis worker. For production scalability, use the Docker/RQ deployment supplied in the main project.

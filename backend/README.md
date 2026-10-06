# LegalMind Backend — Phase 3

FastAPI backend for Phase 1–3: legal document ingestion, retrieval, reranking and evidence-grounded RAG.

## Run

```powershell
copy .env.example .env
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Swagger: http://127.0.0.1:8000/docs

## RAG provider

Default is `LLM_PROVIDER=mock`, a deterministic extractive provider so the project works without an external API key.

For an OpenAI-compatible provider, set:

```env
LLM_PROVIDER=openai-compatible
LLM_API_KEY=...
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

The provider interface can be replaced without changing the RAG pipeline.

## Phase 3 flow

Query classifier → hybrid retrieval → reranking → token-budget evidence selection → constrained prompt → provider → citation verification → coverage/confidence → safe insufficient-evidence response.

Documents are treated as untrusted data. Every answer includes a not-legal-advice disclaimer.

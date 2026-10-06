# LegalMind Phase 2 — What was added to Phase 1

## Backend
- Sentence Transformer embeddings in `chunk_embeddings`.
- Default legal-domain embedding model: `ahb-sjsu/lebse` (768 dimensions).
- pgvector HNSW cosine index.
- BM25 keyword retrieval with an exact phrase boost.
- Semantic vector retrieval.
- Hybrid Reciprocal Rank Fusion with `k=60`.
- Cross-encoder reranking of up to 50 candidates down to the requested top-K.
- Configurable reranker model, default `cross-encoder/ms-marco-MiniLM-L6-v2`.
- Court/category/date filters.
- `retrieval_events` audit table.
- `POST /api/v1/search`.
- `GET /api/v1/chunks/{chunk_id}` for source passage highlighting.
- Re-index command: `backend/scripts/reindex.py`.
- Judgment-date field with a Phase-2 baseline date heuristic.
- Gold-set template and retrieval evaluation script.

## Frontend
- Search Cases page.
- Keyword / semantic / hybrid mode toggle.
- Court/category/date filters.
- Reranking toggle.
- Relevance score explanation.
- Provenance fields: document/page/chunk/section.
- Open evidence directly at the correct page and highlight the retrieved chunk.

## Testing
- RRF unit tests.
- Retrieval integration-test placeholders R-01 through R-06, gated behind PostgreSQL.
- Gold-set template for approximately 30 documents / 50 queries.
- Evaluation script for Precision@K, Recall@K, MRR and NDCG.

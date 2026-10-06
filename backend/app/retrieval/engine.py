import re
import threading
from datetime import date
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy import select
from sqlalchemy.orm import Session
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.models.document import Chunk, Document, DocumentPage, Section
from app.models.retrieval import ChunkEmbedding

_model = None
_reranker = None
_lock = threading.Lock()


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def get_embedding_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                try:
                    _model = SentenceTransformer(settings.EMBEDDING_MODEL)
                except Exception as exc:
                    fallback = getattr(settings, "EMBEDDING_FALLBACK_MODEL", "sentence-transformers/all-mpnet-base-v2")
                    if fallback == settings.EMBEDDING_MODEL:
                        raise
                    import logging
                    logging.getLogger(__name__).warning(
                        "Embedding model %s unavailable; falling back to %s: %s",
                        settings.EMBEDDING_MODEL, fallback, exc
                    )
                    _model = SentenceTransformer(fallback)
                dim = _model.get_sentence_embedding_dimension()
                if dim != settings.EMBEDDING_DIMENSION:
                    raise RuntimeError(
                        f"Embedding model dimension {dim} does not match configured database dimension {settings.EMBEDDING_DIMENSION}."
                    )
    return _model


def get_reranker():
    global _reranker
    if _reranker is None:
        with _lock:
            if _reranker is None:
                _reranker = CrossEncoder(settings.RERANKER_MODEL)
    return _reranker


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def index_chunks(db: Session, chunks: list[Chunk] | None = None, commit: bool = True):
    if chunks is None:
        chunks = db.scalars(select(Chunk).order_by(Chunk.chunk_index)).all()
    if not chunks:
        return 0
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)
    count = 0
    for chunk, vector in zip(chunks, vectors):
        existing = db.scalar(select(ChunkEmbedding).where(ChunkEmbedding.chunk_id == chunk.id))
        if existing:
            existing.embedding = vector
            existing.model_name = settings.EMBEDDING_MODEL
            existing.dimension = len(vector)
        else:
            db.add(ChunkEmbedding(
                id=__import__("uuid").uuid4().hex,
                chunk_id=chunk.id,
                embedding=vector,
                model_name=settings.EMBEDDING_MODEL,
                dimension=len(vector),
            ))
        count += 1
    if commit:
        db.commit()
    return count


def _filtered_chunks(db: Session, filters: dict):
    stmt = select(Chunk, Document, DocumentPage, Section).join(Document, Chunk.document_id == Document.id).join(DocumentPage, Chunk.page_id == DocumentPage.id).outerjoin(Section, Chunk.section_id == Section.id)
    if filters.get("court"):
        stmt = stmt.where(Document.court == filters["court"])
    if filters.get("category"):
        stmt = stmt.where(Document.category == filters["category"])
    if filters.get("date_from"):
        stmt = stmt.where(Document.judgment_date >= date.fromisoformat(filters["date_from"]))
    if filters.get("date_to"):
        stmt = stmt.where(Document.judgment_date <= date.fromisoformat(filters["date_to"]))
    return db.execute(stmt).all()


def keyword_search(db: Session, query: str, filters: dict, limit: int):
    rows = _filtered_chunks(db, filters)
    if not rows: return []
    # PostgreSQL GIN/tsvector is the primary persisted keyword index. BM25 remains a local fallback for tests/non-Postgres DBs.
    try:
        from sqlalchemy import func
        tsq=func.plainto_tsquery('english', query)
        rank=func.ts_rank_cd(Chunk.search_vector, tsq).label('rank')
        stmt=select(Chunk,Document,DocumentPage,Section,rank).join(Document,Chunk.document_id==Document.id).join(DocumentPage,Chunk.page_id==DocumentPage.id).outerjoin(Section,Chunk.section_id==Section.id).where(Chunk.search_vector.op('@@')(tsq))
        if filters.get('court'): stmt=stmt.where(Document.court==filters['court'])
        if filters.get('category'): stmt=stmt.where(Document.category==filters['category'])
        if filters.get('date_from'): stmt=stmt.where(Document.judgment_date>=date.fromisoformat(filters['date_from']))
        if filters.get('date_to'): stmt=stmt.where(Document.judgment_date<=date.fromisoformat(filters['date_to']))
        ranked=db.execute(stmt.order_by(rank.desc()).limit(limit*3)).all()
        if ranked:
            max_score=max(float(r[4]) for r in ranked) or 1.0; q=query.lower().strip(); out=[]
            for c,d,p,s,score in ranked:
                exact=1.0 if q and q in c.text.lower() else 0.0; raw=float(score)+(max_score+1)*1.5*exact
                out.append({'chunk':c,'document':d,'page':p,'section':s,'keyword_score':raw})
            top=max(x['keyword_score'] for x in out) or 1.0
            for x in out: x['keyword_score']=x['keyword_score']/top
            return out[:limit]
    except Exception:
        db.rollback()
    corpus=[_tokens(r[0].text) for r in rows]; scores=BM25Okapi(corpus); scores=scores.get_scores(_tokens(query)); ranked=[]; q=query.lower().strip(); max_score=max(scores) if len(scores) else 0.0
    for idx,score in enumerate(scores):
        chunk,doc,page,section=rows[idx]; exact=1.0 if q and q in chunk.text.lower() else 0.0; raw=float(score)+(max_score+1)*1.5*exact; ranked.append((raw,exact,chunk,doc,page,section))
    ranked.sort(key=lambda x:(x[0],x[1]),reverse=True); top_raw=max((x[0] for x in ranked),default=1.0) or 1.0
    return [{'chunk':x[2],'document':x[3],'page':x[4],'section':x[5],'keyword_score':float(x[0]/top_raw)} for x in ranked[:limit]]


def semantic_search(db: Session, query: str, filters: dict, limit: int):
    query_vec = embed_texts([query])[0]
    distance = ChunkEmbedding.embedding.cosine_distance(query_vec).label("distance")
    stmt = select(ChunkEmbedding, Chunk, Document, DocumentPage, Section, distance).join(Chunk, ChunkEmbedding.chunk_id == Chunk.id).join(Document, Chunk.document_id == Document.id).join(DocumentPage, Chunk.page_id == DocumentPage.id).outerjoin(Section, Chunk.section_id == Section.id)
    if filters.get("court"):
        stmt = stmt.where(Document.court == filters["court"])
    if filters.get("category"):
        stmt = stmt.where(Document.category == filters["category"])
    if filters.get("date_from"):
        stmt = stmt.where(Document.judgment_date >= date.fromisoformat(filters["date_from"]))
    if filters.get("date_to"):
        stmt = stmt.where(Document.judgment_date <= date.fromisoformat(filters["date_to"]))
    rows = db.execute(stmt.order_by(distance).limit(limit)).all()
    return [{"chunk": r[1], "document": r[2], "page": r[3], "section": r[4], "semantic_score": float(max(0.0, 1.0 - r[5]))} for r in rows]


def rrf_fuse(keyword: list[dict], semantic: list[dict], limit: int):
    by_id = {}
    for rank, item in enumerate(keyword, start=1):
        cid = item["chunk"].id
        by_id.setdefault(cid, {**item, "keyword_score": item.get("keyword_score", 0.0), "semantic_score": 0.0, "rrf_score": 0.0})
        by_id[cid]["rrf_score"] += 1.0 / (settings.RRF_K + rank)
    for rank, item in enumerate(semantic, start=1):
        cid = item["chunk"].id
        if cid not in by_id:
            by_id[cid] = {**item, "keyword_score": 0.0, "semantic_score": item.get("semantic_score", 0.0), "rrf_score": 0.0}
        else:
            by_id[cid]["semantic_score"] = item.get("semantic_score", 0.0)
        by_id[cid]["rrf_score"] += 1.0 / (settings.RRF_K + rank)
    return sorted(by_id.values(), key=lambda x: x["rrf_score"], reverse=True)[:limit]


def rerank(query: str, candidates: list[dict], limit: int):
    if not candidates:
        return []
    model = get_reranker()
    pairs = [(query, c["chunk"].text) for c in candidates]
    scores = model.predict(pairs, show_progress_bar=False)
    for c, score in zip(candidates, scores):
        c["rerank_score"] = float(score)
    candidates.sort(key=lambda x: x.get("rerank_score", float("-inf")), reverse=True)
    return candidates[:limit]

import textwrap
import logging
import re
import time
import uuid
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status, Query, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document, DocumentPage, Entity, Section
from app.models.retrieval import RetrievalEvent
from app.models.document import Chunk
from app.schemas.document import DocumentSummary, DocumentOut, PageOut, EntityOut, SectionOut, UploadAccepted
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.schemas.ask import AskRequest
from app.services.processor import process_document
from app.retrieval.engine import keyword_search, semantic_search, rrf_fuse, rerank
from app.rag.pipeline import answer_question
from app.models.rag import RagEvent
from app.schemas.intelligence import SimilarRequest, CompareRequest
from app.intelligence.service import similar_cases, extract_issues, build_timeline, compare_cases
from app.core.security import require_role, _role, make_session, session_role
from app.evaluation import run_evaluation, seed_cases, export_results
from app.models.evaluation import EvaluationResult

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        return {"status": "ok", "phase": 5, "database": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail={"error":"database_unavailable", "message":"Database is unavailable."})

@router.post("/auth/login")
async def login(payload: dict):
    username=str(payload.get("username") or "user")
    password=str(payload.get("password") or "")
    role=_role(password)
    if not role:
        raise HTTPException(status_code=401, detail={"error":"invalid_credentials","message":"Invalid administrator/evaluator credentials."})
    response=JSONResponse({"authenticated":True,"username":username,"role":role})
    response.set_cookie("legalmind_session", make_session(role), httponly=True, secure=False, samesite="lax", max_age=settings.AUTH_SESSION_TTL_SECONDS)
    return response

@router.post("/auth/logout")
def logout():
    response=JSONResponse({"authenticated":False})
    response.delete_cookie("legalmind_session")
    return response

@router.get("/auth/me")
def auth_me(request: Request):
    role=session_role(request.cookies.get("legalmind_session"))
    return {"authenticated":bool(role),"role":role}

@router.post("/documents/upload", response_model=UploadAccepted, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(background: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail={"error":"invalid_file_type", "message":"Only PDF files are accepted."})
    filename = Path(file.filename or "document.pdf").name
    filename = re.sub(r"[^A-Za-z0-9._ -]", "_", filename)[:180] or "document.pdf"
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    doc_id = str(uuid.uuid4()); stored = settings.upload_path / f"{doc_id}.pdf"; stored.parent.mkdir(parents=True, exist_ok=True)
    total=0; first=b""
    try:
        with stored.open("wb") as out:
            while True:
                chunk=await file.read(1024*1024)
                if not chunk: break
                if not first: first=chunk[:8]
                total += len(chunk)
                if total > max_bytes:
                    out.close(); stored.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail={"error":"file_too_large", "message":f"File exceeds {settings.MAX_UPLOAD_MB} MB limit."})
                out.write(chunk)
    finally:
        await file.close()
    if first[:5] != b"%PDF-":
        stored.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail={"error":"invalid_pdf_signature", "message":"File content is not a valid PDF signature."})
    doc = Document(id=doc_id, filename=filename, title=Path(filename).stem, status="uploading", file_path=str(stored), file_size=total)
    db.add(doc); db.commit()
    if settings.USE_WORKER:
        try:
            from app.queue import enqueue_document; enqueue_document(doc_id)
        except Exception:
            logger.exception("Worker enqueue failed; falling back to background processing"); background.add_task(process_document, doc_id)
    else: background.add_task(process_document, doc_id)
    return {"id": doc_id, "status":"uploading", "message":"Document accepted and processing started."}

@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), sort: str = Query("created_at_desc", pattern="^(created_at_desc|created_at_asc|title_asc|title_desc|date_desc|date_asc)$"), status_filter: str|None = Query(None, alias="status"), category: str|None = None, q: str|None = None, db: Session = Depends(get_db)):
    stmt=select(Document)
    if status_filter: stmt=stmt.where(Document.status==status_filter)
    if category: stmt=stmt.where(Document.category==category)
    if q:
        like=f"%{q.strip()}%"; stmt=stmt.where((Document.title.ilike(like)) | (Document.filename.ilike(like)) | (Document.case_number.ilike(like)))
    order={"created_at_desc":Document.created_at.desc(),"created_at_asc":Document.created_at.asc(),"title_asc":Document.title.asc(),"title_desc":Document.title.desc(),"date_desc":Document.judgment_date.desc().nullslast(),"date_asc":Document.judgment_date.asc().nullsfirst()}[sort]
    return db.scalars(stmt.order_by(order).offset((page-1)*page_size).limit(page_size)).all()

@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"error":"not_found", "message":"Document not found."})
    entities = []
    for e in db.scalars(select(Entity).where(Entity.document_id == document_id)).all():
        page = db.get(DocumentPage, e.page_id) if e.page_id else None
        entities.append(EntityOut(id=e.id, label=e.label, text=e.text, page_number=page.page_number if page else None, confidence=e.confidence))
    sections = []
    for s in db.scalars(select(Section).where(Section.document_id == document_id)).all():
        page = db.get(DocumentPage, s.page_id) if s.page_id else None
        sections.append(SectionOut(id=s.id, section_type=s.section_type, text=s.text, page_number=page.page_number if page else None, confidence=s.confidence))
    return DocumentOut.model_validate(doc, from_attributes=True).model_copy(update={"entities":entities, "sections":sections})

@router.get("/documents/{document_id}/pages/{page}", response_model=PageOut)
def get_page(document_id: str, page: int, db: Session = Depends(get_db)):
    item = db.scalar(select(DocumentPage).where(DocumentPage.document_id == document_id, DocumentPage.page_number == page))
    if not item:
        raise HTTPException(status_code=404, detail={"error":"page_not_found", "message":"Page not found."})
    return item

@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db), role: str = Depends(require_role("admin"))):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"error":"not_found", "message":"Document not found."})
    path = Path(doc.file_path)
    db.delete(doc)
    db.commit()
    if path.exists():
        path.unlink()
    return {"deleted": True, "id": document_id}


def _result(item: dict) -> SearchResult:
    c, d, p, s = item["chunk"], item["document"], item["page"], item.get("section")
    snippet = re.sub(r"\s+", " ", c.text).strip()
    if len(snippet) > 360:
        snippet = snippet[:357].rsplit(" ", 1)[0] + "…"
    return SearchResult(
        chunk_id=c.id, document_id=d.id, page_id=p.id, section_id=s.id if s else None,
        case_title=d.title or d.filename, court=d.court, category=d.category,
        page_number=p.page_number, section_type=s.section_type if s else None, snippet=snippet,
        keyword_score=float(item.get("keyword_score", 0.0)), semantic_score=float(item.get("semantic_score", 0.0)),
        rrf_score=float(item.get("rrf_score", 0.0)), rerank_score=item.get("rerank_score")
    )

@router.get("/chunks/{chunk_id}")
def get_chunk(chunk_id: str, db: Session = Depends(get_db)):
    chunk = db.get(Chunk, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail={"error":"chunk_not_found", "message":"Search passage not found."})
    page = db.get(DocumentPage, chunk.page_id) if chunk.page_id else None
    return {"id": chunk.id, "document_id": chunk.document_id, "page_id": chunk.page_id, "section_id": chunk.section_id, "text": chunk.text, "page_number": page.page_number if page else None}

@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, db: Session = Depends(get_db)):
    started = time.perf_counter()
    filters = {k:v for k,v in {"court":request.court,"category":request.category,"date_from":request.date_from,"date_to":request.date_to}.items() if v}
    candidate_limit = min(max(settings.RETRIEVAL_CANDIDATES, request.top_k), 50)
    if request.mode.value == "keyword":
        candidates = keyword_search(db, request.query, filters, candidate_limit)
    elif request.mode.value == "semantic":
        candidates = semantic_search(db, request.query, filters, candidate_limit)
    else:
        keyword = keyword_search(db, request.query, filters, candidate_limit)
        semantic = semantic_search(db, request.query, filters, candidate_limit)
        candidates = rrf_fuse(keyword, semantic, candidate_limit)
    retrieved_ids = [x["chunk"].id for x in candidates]
    if request.rerank and candidates:
        candidates = rerank(request.query, candidates, request.top_k)
    else:
        candidates = candidates[:request.top_k]
    reranked_ids = [x["chunk"].id for x in candidates]
    latency_ms = int((time.perf_counter() - started) * 1000)
    db.add(RetrievalEvent(id=str(uuid.uuid4()), query=request.query, mode=request.mode.value, filters=filters, retrieved_ids=retrieved_ids, reranked_ids=reranked_ids, latency_ms=latency_ms))
    db.commit()
    return SearchResponse(query=request.query, mode=request.mode, reranked=request.rerank, results=[_result(x) for x in candidates], candidate_count=len(retrieved_ids), latency_ms=latency_ms)



@router.post("/similar/{document_id}")
def similar(document_id: str, request: SimilarRequest, db: Session = Depends(get_db)):
    result = similar_cases(db, document_id, request.top_k)
    if result is None:
        raise HTTPException(status_code=404, detail={"error":"not_found", "message":"Document not found."})
    return {"document_id": document_id, "results": result}

@router.get("/documents/{document_id}/issues")
def document_issues(document_id: str, db: Session = Depends(get_db)):
    if not db.get(Document, document_id):
        raise HTTPException(status_code=404, detail={"error":"not_found", "message":"Document not found."})
    return {"document_id": document_id, "issues": extract_issues(db, document_id)}

@router.get("/documents/{document_id}/timeline")
def document_timeline(document_id: str, db: Session = Depends(get_db)):
    if not db.get(Document, document_id):
        raise HTTPException(status_code=404, detail={"error":"not_found", "message":"Document not found."})
    return {"document_id": document_id, "events": build_timeline(db, document_id)}

@router.post("/compare")
def compare(request: CompareRequest, db: Session = Depends(get_db)):
    result = compare_cases(db, request.document_a_id, request.document_b_id)
    if result is None:
        raise HTTPException(status_code=404, detail={"error":"not_found", "message":"One or both documents were not found."})
    return result

@router.get("/nlp/model")
def nlp_model_info():
    return {"model": settings.LEGAL_NER_MODEL, "version": settings.LEGAL_NLP_VERSION, "enabled": settings.ENABLE_LEGAL_TRANSFORMER_NLP, "task":"legal NER with transformer fallback to baseline regex"}

@router.post("/ask")
def ask(request: AskRequest, db: Session = Depends(get_db)):
    question = request.question.strip()
    filters = {k:v for k,v in {"court":request.court, "category":request.category, "date_from":request.date_from, "date_to":request.date_to}.items() if v}
    result = answer_question(db, question, filters)
    db.add(RagEvent(id=str(uuid.uuid4()), query=question, query_type=result["query_type"], evidence_ids=[e["chunk_id"] for e in result["evidence"]], citation_ids=[c["raw"] for c in result["citations"]], model_name=result["provider"], model_version=result["model_version"], latency_ms=result["latency_ms"], coverage=result["coverage"], confidence=result["confidence"], insufficient_evidence=result["insufficient_evidence"]))
    db.commit()
    result["disclaimer"] = "Not legal advice. LegalMind provides document-grounded research assistance and may be incomplete or incorrect."
    if request.stream:
        import json as _json
        def events():
            yield f"data: {_json.dumps({'type':'answer','text':result['answer']})}\n\n"
            yield f"data: {_json.dumps({'type':'metadata','citations':result['citations'],'confidence':result['confidence'],'coverage':result['coverage'],'insufficient_evidence':result['insufficient_evidence'],'disclaimer':result['disclaimer']})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(events(), media_type='text/event-stream')
    return result


@router.get("/analytics")
def analytics(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    role: str = Depends(require_role("admin", "evaluator")),
):
    from sqlalchemy import func, extract
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail={"error": "invalid_date_range", "message": "date_from must not be after date_to."})

    start = datetime.combine(date_from, datetime_time.min, tzinfo=timezone.utc) if date_from else None
    end = datetime.combine(date_to + timedelta(days=1), datetime_time.min, tzinfo=timezone.utc) if date_to else None

    def in_range(statement, column):
        if start:
            statement = statement.where(column >= start)
        if end:
            statement = statement.where(column < end)
        return statement

    docs_stmt = select(Document)
    docs = db.scalars(in_range(docs_stmt, Document.created_at)).all()
    by_court = {}
    by_category = {}
    by_year = {}
    for doc in docs:
        court = str(doc.court or "Unknown")
        category = str(doc.category or "Unknown")
        year = str(doc.judgment_date.year if doc.judgment_date else "Unknown")
        by_court[court] = by_court.get(court, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
        by_year[year] = by_year.get(year, 0) + 1

    doc_ids = [doc.id for doc in docs]
    entity_counts = {}
    if doc_ids:
        for label, count in db.query(Entity.label, func.count()).filter(Entity.document_id.in_(doc_ids)).group_by(Entity.label).all():
            entity_counts[str(label)] = count

    retrieval_filter = in_range(select(RetrievalEvent), RetrievalEvent.created_at).subquery()
    rag_filter = in_range(select(RagEvent), RagEvent.created_at).subquery()
    top_queries = db.execute(
        select(retrieval_filter.c.query, func.count().label("count"), func.max(retrieval_filter.c.created_at).label("last_seen"))
        .group_by(retrieval_filter.c.query)
        .order_by(func.count().desc(), func.max(retrieval_filter.c.created_at).desc())
        .limit(8)
    ).all()
    activity_rows = db.execute(
        select(func.date(retrieval_filter.c.created_at).label("day"), func.count().label("count"))
        .group_by(func.date(retrieval_filter.c.created_at))
        .order_by(func.date(retrieval_filter.c.created_at))
    ).all()
    def is_qa_artifact(doc):
        name=(doc.filename or "").lower()
        return any(marker in name for marker in ("sample_judgment", "invalid-security-probe", "e2e_", "qa_", "fixture"))
    qa_docs=[d for d in docs if is_qa_artifact(d)]
    prod_docs=[d for d in docs if not is_qa_artifact(d)]
    total=len(prod_docs); ready=sum(d.status=='ready' for d in prod_docs); failed=sum(d.status=='failed' for d in prod_docs)
    processing_times=[(d.processing_finished_at-d.processing_started_at).total_seconds()*1000 for d in prod_docs if d.processing_started_at and d.processing_finished_at]
    avg_ingestion=sum(processing_times)/len(processing_times) if processing_times else 0
    search_avg = db.scalar(select(func.avg(retrieval_filter.c.latency_ms))) or 0
    ask_avg = db.scalar(select(func.avg(rag_filter.c.latency_ms))) or 0
    return {
        "filters": {"date_from": date_from.isoformat() if date_from else None, "date_to": date_to.isoformat() if date_to else None},
        "corpus": {"documents": total, "by_court": by_court, "by_category": by_category, "by_year": by_year, "entity_counts": entity_counts, "qa_artifacts": len(qa_docs)},
        "processing": {"success_rate": ready/total if total else 0, "failure_rate": failed/total if total else 0, "avg_ingestion_ms": avg_ingestion, "production_documents": total, "qa_artifacts": len(qa_docs), "qa_failed": sum(d.status=='failed' for d in qa_docs)},
        "latency": {"search_avg_ms": float(search_avg), "ask_avg_ms": float(ask_avg)},
        "search_activity": [{"date": str(row.day), "count": row.count} for row in activity_rows],
        "top_queries": [{"query": row.query, "count": row.count, "last_seen": row.last_seen.isoformat() if row.last_seen else None} for row in top_queries],
    }

@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    from sqlalchemy import func
    return {
        "documents_total": db.query(func.count(Document.id)).scalar() or 0,
        "documents_ready": db.query(func.count(Document.id)).filter(Document.status == "ready").scalar() or 0,
        "documents_processing": db.query(func.count(Document.id)).filter(Document.status.in_(("uploading", "processing", "indexing"))).scalar() or 0,
        "documents_failed": db.query(func.count(Document.id)).filter(Document.status == "failed").scalar() or 0,
        "search_events": db.query(func.count(RetrievalEvent.id)).scalar() or 0,
        "ask_events": db.query(func.count(RagEvent.id)).scalar() or 0,
        "evaluation_results": db.query(func.count(EvaluationResult.id)).scalar() or 0,
    }

@router.post("/evaluation/run")
def evaluation_run(db: Session = Depends(get_db), role: str = Depends(require_role("admin","evaluator"))):
    seed_cases(db); run_id=run_evaluation(db); return {"run_id":run_id,"status":"completed"}

@router.get("/evaluation/results")
def evaluation_results(db: Session = Depends(get_db), run_id: str|None = None, role: str = Depends(require_role("admin","evaluator"))):
    stmt=select(EvaluationResult).order_by(EvaluationResult.created_at.desc())
    if run_id: stmt=stmt.where(EvaluationResult.run_id==run_id)
    rows=db.scalars(stmt).all()
    return [{"run_id":r.run_id,"case_id":r.case_id,"metric":r.metric,"value":r.value,"latency_ms":r.latency_ms,"details":r.details} for r in rows]

@router.get("/evaluation/export")
def evaluation_export(fmt: str = Query("json", pattern="^(json|csv)$"), run_id: str|None = None, db: Session = Depends(get_db), role: str = Depends(require_role("admin","evaluator"))):
    body,media=export_results(db,fmt,run_id); return PlainTextResponse(body,media_type=media,headers={"Content-Disposition":f"attachment; filename=legalmind-evaluation.{fmt}"})

@router.post("/admin/retention")
def retention_cleanup(db: Session = Depends(get_db), role: str = Depends(require_role("admin"))):
    from app.retention import cleanup
    if settings.RETENTION_DAYS <= 0: return {"deleted":0,"message":"RETENTION_DAYS is disabled."}
    return {"deleted":cleanup(),"retention_days":settings.RETENTION_DAYS}

import logging
import uuid
import re
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.document import Document, DocumentPage, Entity, Section, Chunk
from app.services.pdf_service import extract_pdf
from app.nlp.entities import extract_entities
from app.nlp.classification import classify_case
from app.nlp.sections import detect_sections
from app.nlp.chunking import chunk_text
from app.retrieval.engine import index_chunks
from app.core.config import settings
from app.nlp.legal_transformer import extract_legal_entities

logger = logging.getLogger(__name__)

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b"),
    re.compile(rf"\b(?:{MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b", re.I),
    re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})\s+\d{{4}}\b", re.I),
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),
]


def _parse_date(raw: str):
    value = raw.strip().replace(".", "/")
    value = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", value, flags=re.I)
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%B %d, %Y", "%d %B %Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _first_date(text: str):
    preferred = re.search(r"(?:date\s+of\s+(?:judgment|judgement)|judgment\s+date|dated)\s*[:\-]?\s*(.{0,40})", text, re.I)
    if preferred:
        for pat in DATE_PATTERNS:
            m = pat.search(preferred.group(1))
            if m:
                parsed = _parse_date(m.group(0))
                if parsed: return parsed
    matches = []
    for pat in DATE_PATTERNS:
        matches.extend(pat.finditer(text))
    for m in sorted(matches, key=lambda x: x.start()):
        parsed = _parse_date(m.group(0))
        if parsed: return parsed
    return None


def _extract_case_number(text: str, entities):
    for e in entities:
        if e.get("label") == "CASE_NUMBER":
            return e.get("text")
    patterns = [
        r"\b(?:Civil|Criminal|Crl\.?|W\.P\.?|Writ|SLP|Special Leave|Appeal)[\w./() -]{1,60}\b",
        r"\b(?:Case|Petition|Appeal)\s*(?:No\.?|Number)\s*[:.]?\s*[A-Za-z0-9./() -]{2,50}",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m: return m.group(0).strip(" .,:;")
    return None


def _extract_court(text: str):
    patterns = [
        r"Supreme Court of India",
        r"Supreme Court",
        r"High Court of [A-Za-z .]+",
        r"High Court",
        r"District Court",
        r"Sessions Court",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m: return re.sub(r"\s+", " ", m.group(0)).strip()
    return None


def _extract_title(text: str, filename: str):
    head = [re.sub(r"\s+", " ", x).strip(" .:-") for x in text.splitlines()[:50]]
    head = [x for x in head if 5 <= len(x) <= 220]
    for line in head:
        if re.search(r"\b(?:v\.?|vs\.?|versus)\b", line, re.I) and not re.search(r"supreme court|high court|judgment|judgement|order", line, re.I):
            return line
    return filename.rsplit(".", 1)[0]


def _merged_segments(pages):
    segments = []
    previous_type = None
    for p in pages:
        detected = detect_sections(p["text"])
        if not detected:
            continue
        for section_type, section_text, confidence in detected:
            stype = previous_type if section_type == "GENERAL" and previous_type else section_type
            segments.append({"page": p, "section_type": stype, "text": section_text, "confidence": confidence})
            if stype != "GENERAL": previous_type = stype
    merged = []
    for seg in segments:
        if merged and merged[-1]["section_type"] == seg["section_type"]:
            merged[-1]["segments"].append(seg)
            merged[-1]["text"] += "\n\n" + seg["text"]
            merged[-1]["confidence"] = max(merged[-1]["confidence"], seg["confidence"])
        else:
            merged.append({"section_type": seg["section_type"], "text": seg["text"], "confidence": seg["confidence"], "segments":[seg]})
    return merged


def process_document(document_id: str):
    from app.db.session import SessionLocal
    db: Session = SessionLocal()
    doc = None
    try:
        doc = db.get(Document, document_id)
        if not doc: return
        doc.status = "processing"
        doc.processing_started_at = datetime.utcnow()
        db.commit()
        t0=time.perf_counter(); pages = extract_pdf(doc.file_path); logger.info("stage=pdf_extract document_id=%s duration_ms=%d", document_id, int((time.perf_counter()-t0)*1000))
        doc.page_count = len(pages)
        all_text = "\n\n".join(p["text"] for p in pages)
        t0=time.perf_counter(); category, confidence = classify_case(all_text); logger.info("stage=classification document_id=%s duration_ms=%d", document_id, int((time.perf_counter()-t0)*1000))
        doc.category, doc.category_confidence = category, confidence
        doc.court = _extract_court(all_text) or doc.court
        doc.judgment_date = _first_date(all_text) or doc.judgment_date
        doc.title = _extract_title(all_text, doc.filename)

        # NER is run page-by-page so source-page provenance is retained.
        page_entities = {}
        t0=time.perf_counter()
        for p in pages:
            if settings.ENABLE_LEGAL_TRANSFORMER_NLP:
                legal_entities, nlp_version = extract_legal_entities(p["text"])
                doc.nlp_model_version = nlp_version
                doc.nlp_method = "transformer" if nlp_version != "baseline-regex-v1" else "baseline"
            else:
                legal_entities = [e.__dict__ for e in extract_entities(p["text"])]
                doc.nlp_model_version = "baseline-regex-v1"; doc.nlp_method = "baseline"
            page_entities[p["page_number"]] = legal_entities
            if not doc.case_number:
                doc.case_number = _extract_case_number(p["text"], legal_entities)

        logger.info("stage=ner document_id=%s duration_ms=%d", document_id, int((time.perf_counter()-t0)*1000))
        for p in pages:
            page = DocumentPage(id=str(uuid.uuid4()), document_id=doc.id, **p)
            db.add(page); db.flush()
            for ent in page_entities[p["page_number"]]:
                db.add(Entity(id=str(uuid.uuid4()), document_id=doc.id, page_id=page.id, label=ent["label"], text=ent["text"], start_offset=ent.get("start"), end_offset=ent.get("end"), confidence=ent.get("confidence", 0.75)))

        # Merge sections across page boundaries while keeping chunk-level page provenance.
        t0=time.perf_counter()
        for group in _merged_segments(pages):
            first_page = db.scalar(select(DocumentPage).where(DocumentPage.document_id==doc.id, DocumentPage.page_number==group["segments"][0]["page"]["page_number"]))
            section = Section(id=str(uuid.uuid4()), document_id=doc.id, page_id=first_page.id if first_page else None, section_type=group["section_type"], text=group["text"], confidence=group["confidence"])
            db.add(section); db.flush()
            for idx, seg in enumerate(group["segments"]):
                page = db.scalar(select(DocumentPage).where(DocumentPage.document_id==doc.id, DocumentPage.page_number==seg["page"]["page_number"]))
                for piece in chunk_text(seg["text"]):
                    chunk = Chunk(id=str(uuid.uuid4()), document_id=doc.id, page_id=page.id if page else None, section_id=section.id, chunk_index=idx, text=piece)
                    db.add(chunk)
                    idx += 1

        logger.info("stage=sections_chunks document_id=%s duration_ms=%d", document_id, int((time.perf_counter()-t0)*1000))
        # Make the indexing state durable and visible before expensive embeddings begin.
        doc.status = "indexing"
        db.commit()
        db.refresh(doc)
        if settings.ENABLE_EMBEDDINGS:
            t0=time.perf_counter(); chunks = db.scalars(select(Chunk).where(Chunk.document_id==doc.id)).all()
            index_chunks(db, chunks, commit=False); logger.info("stage=embeddings document_id=%s duration_ms=%d", document_id, int((time.perf_counter()-t0)*1000))
        doc.status = "ready"
        doc.processing_finished_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc:
            doc.status = "failed"; doc.error_message = str(exc)[:2000]; doc.processing_finished_at = datetime.utcnow(); db.commit()
        logger.exception("Document processing failed for %s", document_id)
    finally:
        db.close()

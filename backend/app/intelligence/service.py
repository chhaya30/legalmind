import math, re, time, uuid
from collections import defaultdict
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentPage, Entity, Section, Chunk
from app.models.retrieval import ChunkEmbedding

ISSUE_PATTERNS = [
    r"(?:issue|question|point)\s+(?:for determination|before the court)?\s*[:\-]\s*(.+?)(?=\n|$)",
    r"whether\s+(.+?)(?=\?|\n|$)",
]
DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b"),
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b", re.I),
    re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", re.I),
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),
]

def _parse_date(raw):
    value=re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", raw.strip(), flags=re.I).replace('.', '/')
    for fmt in ("%d/%m/%Y","%d-%m-%Y","%d/%m/%y","%B %d, %Y","%d %B %Y","%Y-%m-%d"):
        try: return datetime.strptime(value, fmt).date()
        except ValueError: pass
    return None



def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _tokens(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def _cos(a, b):
    if not a or not b: return 0.0
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(x*x for x in b))
    return float(dot/(na*nb)) if na and nb else 0.0


def _doc_chunks(db, doc_id):
    return db.scalars(select(Chunk).where(Chunk.document_id == doc_id)).all()


def _document_source_page(db, doc_id):
    return db.scalar(
        select(DocumentPage.page_number)
        .join(Chunk, Chunk.page_id == DocumentPage.id)
        .where(Chunk.document_id == doc_id)
        .order_by(Chunk.chunk_index)
        .limit(1)
    )


def document_vector(db, doc_id):
    chunks = _doc_chunks(db, doc_id)
    if not chunks: return None
    ids = [c.id for c in chunks]
    rows = db.scalars(select(ChunkEmbedding).where(ChunkEmbedding.chunk_id.in_(ids))).all()
    vectors = [list(r.embedding) for r in rows if r.embedding is not None]
    if not vectors: return None
    dim = len(vectors[0]); return [sum(v[i] for v in vectors)/len(vectors) for i in range(dim)]


def legal_entities(db, doc_id):
    rows = db.scalars(select(Entity).where(Entity.document_id == doc_id)).all()
    acts, provisions = set(), set()
    for e in rows:
        value = _norm(e.text).lower()
        if e.label in {"ACT", "STATUTE"} or " act" in value:
            acts.add(value)
        if e.label in {"LEGAL_SECTION", "PROVISION"} or re.search(r"\b(section|sec\.|article|art\.)\s*\d", value):
            provisions.add(value)
    return acts, provisions


def similar_cases(db: Session, document_id: str, top_k=5):
    target = db.get(Document, document_id)
    if not target: return None
    target_vec = document_vector(db, document_id)
    target_acts, target_provisions = legal_entities(db, document_id)
    target_page = _document_source_page(db, document_id)
    candidates=[]
    for doc in db.scalars(select(Document).where(Document.id != document_id, Document.status == "ready")).all():
        vec = document_vector(db, doc.id)
        semantic = _cos(target_vec, vec) if target_vec and vec else 0.0
        acts, provisions = legal_entities(db, doc.id)
        act_overlap = len(target_acts & acts) / max(1, len(target_acts | acts))
        prov_overlap = len(target_provisions & provisions) / max(1, len(target_provisions | provisions))
        score = 0.72*semantic + 0.18*act_overlap + 0.10*prov_overlap
        reasons=[]
        if semantic >= .65: reasons.append("Strong document-level semantic similarity")
        if target_acts & acts: reasons.append("Shared Acts/statutes: " + ", ".join(sorted(target_acts & acts)[:4]))
        if target_provisions & provisions: reasons.append("Shared provisions: " + ", ".join(sorted(target_provisions & provisions)[:5]))
        if not reasons: reasons.append("Weak lexical/semantic overlap")
        candidates.append({"document_id":doc.id,"title":doc.title or doc.filename,"court":doc.court,"category":doc.category,"similarity_score":round(score,4),"semantic_score":round(semantic,4),"entity_overlap":round(act_overlap+prov_overlap,4),"why_similar":reasons,"target_page_number":target_page,"source_page_number":_document_source_page(db,doc.id)})
    return sorted(candidates,key=lambda x:x["similarity_score"],reverse=True)[:top_k]


def extract_issues(db, doc_id):
    sections = db.scalars(select(Section).where(Section.document_id == doc_id, Section.section_type == "ISSUES")).all()
    issues=[]
    for s in sections:
        text=s.text
        found=False
        for pat in ISSUE_PATTERNS:
            for m in re.finditer(pat,text,re.I|re.S):
                val=_norm(m.group(1)).strip(" .;:")
                if len(val)>10:
                    page=db.get(DocumentPage,s.page_id) if s.page_id else None
                    issues.append({"issue":val,"section_id":s.id,"page_number":page.page_number if page else None,"source_text":_norm(text)[:700],"confidence":0.9})
                    found=True
        if not found and _norm(text):
            page=db.get(DocumentPage,s.page_id) if s.page_id else None
            for line in text.splitlines():
                line=_norm(line).strip("-• ")
                if len(line)>12:
                    issues.append({"issue":line,"section_id":s.id,"page_number":page.page_number if page else None,"source_text":_norm(text)[:700],"confidence":0.72})
    if not issues:
        # fallback: detect explicit question sentences in the whole case
        pages=db.scalars(select(DocumentPage).where(DocumentPage.document_id==doc_id).order_by(DocumentPage.page_number)).all()
        for p in pages:
            for m in re.finditer(r"\bwhether\s+(.{15,220}?)(?:\?|\.)",p.text,re.I|re.S):
                issues.append({"issue":_norm(m.group(1)),"section_id":None,"page_number":p.page_number,"source_text":_norm(m.group(0)),"confidence":0.65})
                if len(issues)>=10: break
    # dedupe
    seen=set(); out=[]
    for x in issues:
        k=x["issue"].lower()
        if k not in seen: seen.add(k); out.append(x)
    return out[:15]


def build_timeline(db, doc_id):
    pages=db.scalars(select(DocumentPage).where(DocumentPage.document_id==doc_id).order_by(DocumentPage.page_number)).all()
    events=[]
    for p in pages:
        for pat in DATE_PATTERNS:
            for m in pat.finditer(p.text):
                raw=m.group(0)
                dt=_parse_date(raw)
                if not dt: continue
                start=max(0,m.start()-100); end=min(len(p.text),m.end()+180)
                context=_norm(p.text[start:end])
                events.append({"date":dt.isoformat(),"date_text":raw,"event":context,"page_number":p.page_number,"source_page_id":p.id})
    # de-duplicate same date/context
    seen=set(); out=[]
    for e in sorted(events,key=lambda x:(x["date"],x["page_number"])):
        k=(e["date"],e["event"][:100])
        if k not in seen: seen.add(k); out.append(e)
    return out[:100]


def _section_blocks(db, doc_id, section):
    stmt=select(Section, DocumentPage).outerjoin(DocumentPage, Section.page_id==DocumentPage.id).where(Section.document_id==doc_id, Section.section_type==section).order_by(DocumentPage.page_number.nulls_last())
    return db.execute(stmt).all()

def _field_text(db, doc_id, field):
    return "\n\n".join(_norm(s.text) for s,p in _section_blocks(db, doc_id, field))[:5000]

def _field_source(db, doc_id, section):
    rows=_section_blocks(db, doc_id, section)
    pages={p.page_number for _,p in rows if p}
    for sec,_ in rows:
        chunk_rows=db.scalars(select(Chunk).where(Chunk.section_id==sec.id)).all()
        for ch in chunk_rows:
            if ch.page_id:
                page=db.get(DocumentPage,ch.page_id)
                if page: pages.add(page.page_number)
    ordered=sorted(pages)
    return {"document_id":doc_id,"page_number":ordered[0] if ordered else None,"pages":ordered}

def _aligned_issues(db, doc_id):
    return [x["issue"] for x in extract_issues(db,doc_id)]

def _compare_texts(ta,tb):
    toks_a=_tokens(ta); toks_b=_tokens(tb); return len(toks_a&toks_b)/max(1,len(toks_a|toks_b))

def compare_cases(db, a_id, b_id):
    a=db.get(Document,a_id); b=db.get(Document,b_id)
    if not a or not b: return None
    fields={"facts":"FACTS","issues":"ISSUES","laws":"LAW","reasoning":"REASONING","outcome":"JUDGMENT"}
    result={"case_a":{"document_id":a.id,"title":a.title or a.filename},"case_b":{"document_id":b.id,"title":b.title or b.filename},"similarities":[],"differences":[],"fields":[]}
    for name,section in fields.items():
        ta=_field_text(db,a_id,section); tb=_field_text(db,b_id,section)
        if name=="issues":
            ia=_aligned_issues(db,a_id); ib=_aligned_issues(db,b_id); ta="\n".join(ia); tb="\n".join(ib)
        if name=="laws" and (not ta or not tb):
            aa,ap=legal_entities(db,a_id); ba,bp=legal_entities(db,b_id); ta="; ".join(sorted(aa|ap)); tb="; ".join(sorted(ba|bp))
        overlap=_compare_texts(ta,tb); similar=overlap>=0.16
        sa=_field_source(db,a_id,section); sb=_field_source(db,b_id,section)
        field={"field":name,"case_a_text":ta[:1600],"case_b_text":tb[:1600],"overlap":round(overlap,3),"source_a":sa,"source_b":sb}
        result["fields"].append(field)
        (result["similarities"] if similar else result["differences"]).append({"field":name,"explanation":("Substantial overlap after section/issue alignment" if similar else "Material divergence after section/issue alignment"),"source_a":sa,"source_b":sb})
    return result

import re

CITATION_RE = re.compile(r'\[([^\],]+),\s*p\.(\d+),\s*§([^\]]+)\]')

def parse_citations(text: str):
    return [{'doc': m.group(1).strip(), 'page': int(m.group(2)), 'section': m.group(3).strip(), 'raw': m.group(0)} for m in CITATION_RE.finditer(text)]

def verify_citations(text: str, evidence: list[dict]):
    citations = parse_citations(text)
    valid = []
    invalid = []
    for c in citations:
        ok = any(str(e.get('document_id')) == c['doc'] and int(e.get('page_number', -1)) == c['page'] and (e.get('section_type') or 'Document') == c['section'] for e in evidence)
        (valid if ok else invalid).append(c)
    return valid, invalid

def citation_for(e):
    section = e.get('section_type') or 'Document'
    return f"[{e['document_id']}, p.{e['page_number']}, §{section}]"

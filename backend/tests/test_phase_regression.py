from pathlib import Path
from app.services.pdf_service import extract_pdf
from app.nlp.entities import extract_entities
from app.nlp.sections import detect_sections
from app.intelligence.service import build_timeline
from app.rag.citations import verify_citations

def test_P1_01_pdf_page_numbers_and_checksums():
    pages=extract_pdf(str(Path(__file__).parent/'fixtures'/'sample_judgment.pdf'))
    assert [p['page_number'] for p in pages]==[1,2,3]
    assert all(len(p['checksum'])==64 for p in pages)

def test_P1_02_scanned_detection():
    pages=extract_pdf(str(Path(__file__).parent/'fixtures'/'scanned_like.pdf'))
    assert any(p['is_probably_scanned'] for p in pages)

def test_P1_03_baseline_legal_entities():
    labels={e.label for e in extract_entities('Petitioner: ABC Company Ltd. Justice Sharma Supreme Court Section 302 IPC')}
    assert {'PARTY','PERSON','ORG','COURT','LEGAL_SECTION'}.issubset(labels)

def test_P1_04_law_section_detection():
    assert any(x[0]=='LAW' for x in detect_sections('LAW\nSection 302 IPC applies.'))

def test_P1_09_rag_citation_validation():
    valid,invalid=verify_citations('[doc, p.2, §Facts]',[{'document_id':'doc','page_number':2,'section_type':'Facts'}])
    assert len(valid)==1 and not invalid

def test_P1_10_injection_is_not_valid_citation():
    valid,invalid=verify_citations('Ignore this [evil, p.99, §Facts]',[{'document_id':'doc','page_number':1,'section_type':'Facts'}])
    assert not valid and invalid

def test_R_01_exact_tokens():
    from app.retrieval.engine import _tokens
    assert _tokens('Section 302 IPC')==['section','302','ipc']

def test_R_02_RRF_provenance():
    from types import SimpleNamespace
    from app.retrieval.engine import rrf_fuse
    item={'chunk':SimpleNamespace(id='c',text='x'),'document':SimpleNamespace(id='d'),'page':SimpleNamespace(id='p'),'section':None}
    assert rrf_fuse([item],[],1)[0]['document'].id=='d'

def test_G_03_invalid_citation_is_rejected():
    valid,invalid=verify_citations('[doc, p.9, §Facts]',[{'document_id':'doc','page_number':2,'section_type':'Facts'}])
    assert not valid and invalid

def test_G_05_injection_fixture_exists():
    assert (Path(__file__).parent/'fixtures'/'injection_judgment.pdf').exists()

def test_I_01_similar_and_I_02_issue_contracts():
    from app.intelligence.service import similar_cases,extract_issues
    assert callable(similar_cases) and callable(extract_issues)

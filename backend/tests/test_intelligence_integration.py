from app.intelligence.service import similar_cases, extract_issues, build_timeline, compare_cases
from app.nlp.legal_transformer import extract_legal_entities
from app.core.config import settings

def test_I01_similar_cases_callable(): assert callable(similar_cases)
def test_I02_issues_callable(): assert callable(extract_issues)
def test_I03_timeline_callable(): assert callable(build_timeline)
def test_I04_compare_callable(): assert callable(compare_cases)
def test_I05_nlp_versioned(): assert settings.LEGAL_NLP_VERSION

def test_transformer_falls_back_cleanly():
    entities,version=extract_legal_entities('Supreme Court Section 302')
    assert isinstance(entities,list) and version

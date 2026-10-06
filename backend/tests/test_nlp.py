from app.nlp.cleaning import clean_page_text
from app.nlp.entities import extract_entities
from app.nlp.classification import classify_case
from app.nlp.sections import detect_sections
from app.nlp.chunking import chunk_text

def test_cleaning_hyphenation():
    assert "legalmatter" in clean_page_text("legal-\nmatter")

def test_entities():
    text = "Supreme Court decided Section 420 on 12/08/2024 in Civil Appeal 12/2024."
    labels = {e.label for e in extract_entities(text)}
    assert {"COURT", "LEGAL_SECTION", "DATE", "CASE_NUMBER"}.issubset(labels)

def test_classification():
    category, confidence = classify_case("The accused sought bail in a criminal prosecution under the penal code.")
    assert category == "Criminal"
    assert confidence > 0.4

def test_sections_and_chunks():
    sections = detect_sections("FACTS\nThe facts are stated here.\nISSUES\nThe issue is whether.")
    assert any(x[0] == "FACTS" for x in sections)
    assert chunk_text("x" * 5000)

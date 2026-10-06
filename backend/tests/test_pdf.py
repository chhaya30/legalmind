from pathlib import Path
from app.services.pdf_service import extract_pdf

def test_fixture_pdf_preserves_page_numbers_and_checksums():
    path = Path(__file__).parent / "fixtures" / "sample_judgment.pdf"
    pages = extract_pdf(str(path))
    assert [p["page_number"] for p in pages] == [1,2,3]
    assert all(len(p["checksum"]) == 64 for p in pages)
    assert "SUPREME COURT" in pages[0]["text"]

def test_scanned_like_page_is_flagged():
    path = Path(__file__).parent / "fixtures" / "scanned_like.pdf"
    pages = extract_pdf(str(path))
    assert any(p["is_probably_scanned"] for p in pages)

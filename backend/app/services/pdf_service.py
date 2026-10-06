import hashlib
import fitz
from app.nlp.cleaning import clean_page_text, remove_repeated_headers_footers

def extract_pdf(path: str):
    doc = fitz.open(path)
    raw = [page.get_text("text") for page in doc]
    cleaned = [clean_page_text(t) for t in raw]
    cleaned = remove_repeated_headers_footers(cleaned)
    pages = []
    for i, text in enumerate(cleaned, 1):
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        pages.append({"page_number": i, "text": text, "checksum": checksum, "is_probably_scanned": len(text.strip()) < 30})
    return pages

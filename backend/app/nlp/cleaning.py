import re

def clean_page_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    # Remove simple standalone page numbers and common repeated header/footer markers.
    lines = [ln for ln in lines if not re.fullmatch(r"(?:page\s*)?\d{1,4}", ln, flags=re.I)]
    return "\n".join(lines).strip()

def remove_repeated_headers_footers(pages: list[str]) -> list[str]:
    if len(pages) < 3:
        return pages
    counts = {}
    for text in pages:
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        for line in set(lines[:2] + lines[-2:]):
            if 3 <= len(line) <= 120:
                counts[line] = counts.get(line, 0) + 1
    repeated = {line for line, count in counts.items() if count >= max(3, len(pages)//2)}
    return ["\n".join(x for x in p.splitlines() if x.strip() not in repeated).strip() for p in pages]

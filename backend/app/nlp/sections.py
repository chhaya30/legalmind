import re
HEADINGS = {
    "FACTS": ["facts", "brief facts", "background"],
    "ISSUES": ["issues", "questions for determination", "points for determination"],
    "ARGUMENTS": ["arguments", "submissions", "contentions"],
    "LAW": ["law", "laws", "applicable law", "legal provisions", "statutes", "statutory provisions"],
    "REASONING": ["reasoning", "discussion", "analysis", "findings"],
    "JUDGMENT": ["judgment", "order", "decision", "conclusion"],
}

def detect_sections(page_text: str):
    lines = page_text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
        for label, headings in HEADINGS.items():
            if any(normalized == h or normalized.startswith(h + " ") for h in headings):
                hits.append((label, i, line))
                break
    if not hits:
        return [("GENERAL", page_text, 0.4)] if page_text.strip() else []
    out = []
    for idx, (label, start, _) in enumerate(hits):
        end = hits[idx+1][1] if idx + 1 < len(hits) else len(lines)
        body = "\n".join(lines[start:end]).strip()
        if body:
            out.append((label, body, 0.75))
    return out

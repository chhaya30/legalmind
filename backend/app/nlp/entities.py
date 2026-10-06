import re
from dataclasses import dataclass

PATTERNS = {
    "CASE_NUMBER": [r"\b(?:Case|Crl\.?|Civil|W\.P\.?|Writ|Appeal|SLP)[\w./() -]{2,60}\b"],
    "LEGAL_SECTION": [r"\b(?:Section|Sec\.?|Article|Art\.?)\s+\d+[A-Za-z0-9()\-./]*\b"],
    "DATE": [r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b", r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"],
    "ACT": [r"\b[A-Z][A-Za-z &,'-]{2,80}\s+Act,?\s+\d{4}\b"],
    "COURT": [r"\b(?:Supreme Court of India|Supreme Court|High Court(?: of [A-Z][A-Za-z .]+)?|District Court|Sessions Court|Magistrate Court|Court of Appeal)\b"],
    "PARTY": [r"\b(?:Petitioner|Respondent|Appellant|Plaintiff|Defendant|Accused|Complainant)\s*[:\-]?\s*[A-Z][A-Za-z .&-]{2,80}"],
    "PERSON": [r"\b(?:Justice|Hon'?ble Justice|Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+[A-Z][A-Za-z.'-]{2,40}(?:\s+[A-Z][A-Za-z.'-]{2,40}){0,2}"],
    "ORG": [r"\b[A-Z][A-Za-z&. ]{2,80}\s+(?:Ltd\.?|Limited|Corporation|Corporations|University|Commission|Authority|Board|Bank|Company)\b"],
}

@dataclass
class FoundEntity:
    label: str
    text: str
    start: int
    end: int
    confidence: float = 0.78

def extract_entities(text: str) -> list[FoundEntity]:
    found = []
    seen = set()
    for label, patterns in PATTERNS.items():
        for pattern in patterns:
            for m in re.finditer(pattern, text, flags=re.I if label in {"DATE","COURT","PARTY","PERSON"} else 0):
                value = m.group(0).strip(" .,:;\n")
                key = (label, value.lower(), m.start())
                if key in seen or len(value) < 3:
                    continue
                seen.add(key)
                conf = 0.8 if label in {"LEGAL_SECTION","COURT","DATE","PARTY"} else 0.72
                found.append(FoundEntity(label, value, m.start(), m.end(), conf))
    return sorted(found, key=lambda x: x.start)

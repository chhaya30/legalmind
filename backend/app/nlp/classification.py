import re
CATEGORIES = {
    "Criminal": ["murder", "bail", "accused", "fir", "criminal", "penal code", "prosecution"],
    "Civil": ["plaintiff", "defendant", "civil suit", "damages", "injunction"],
    "Property": ["property", "land", "title deed", "possession", "tenant", "lease"],
    "Contract": ["agreement", "contract", "breach", "consideration", "arbitration"],
    "Family": ["divorce", "custody", "maintenance", "matrimonial", "marriage"],
    "Constitutional": ["constitution", "fundamental right", "article 14", "article 19", "article 21", "writ"],
    "Tax": ["tax", "gst", "income tax", "assessment", "customs"],
    "Cyber": ["cyber", "computer", "online fraud", "information technology act", "phishing"],
}

def classify_case(text: str):
    lower = text.lower()
    scores = {}
    for cat, terms in CATEGORIES.items():
        scores[cat] = sum(len(re.findall(re.escape(term), lower)) for term in terms)
    best = max(scores, key=scores.get)
    total = sum(scores.values())
    if total == 0:
        return "Unclassified", 0.25
    confidence = min(0.98, 0.45 + scores[best] / max(total, 1) * 0.5)
    return best, round(confidence, 3)

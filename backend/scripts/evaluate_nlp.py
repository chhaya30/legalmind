"""Compare baseline vs legal-transformer NER on a small labeled JSONL/JSON file.
Expected format: [{"text":"...","entities":[{"text":"...","label":"..."}]}]."""
import json, sys
from pathlib import Path
from app.nlp.entities import extract_entities
from app.nlp.legal_transformer import extract_legal_entities

def score(pred, gold):
    p={(x["text"].lower(),x["label"]) for x in pred}; g={(x["text"].lower(),x["label"]) for x in gold}
    tp=len(p&g); return {"precision":tp/max(1,len(p)),"recall":tp/max(1,len(g)),"f1":2*tp/max(1,len(p)+len(g))}

path=Path(sys.argv[1] if len(sys.argv)>1 else "tests/nlp_gold_set.json")
data=json.loads(path.read_text())
base=[]; trans=[]
for row in data:
    base.extend(score([e.__dict__ for e in extract_entities(row["text"])], row["entities"]).__class__ and [])
# Recompute micro counts
for mode in ("baseline","transformer"):
    tp=pp=gg=0
    for row in data:
        pred=[e.__dict__ for e in extract_entities(row["text"])] if mode=="baseline" else extract_legal_entities(row["text"])[0]
        ps={(e["text"].lower(),e["label"]) for e in pred}; gs={(e["text"].lower(),e["label"]) for e in row["entities"]}
        tp+=len(ps&gs); pp+=len(ps); gg+=len(gs)
    precision=tp/max(1,pp); recall=tp/max(1,gg); f1=2*precision*recall/max(1,precision+recall)
    print(mode, json.dumps({"precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4)}))

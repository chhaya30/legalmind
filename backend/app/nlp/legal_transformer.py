import logging
from functools import lru_cache
from app.core.config import settings
from app.nlp.entities import extract_entities as baseline_entities
logger=logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _pipeline():
    from transformers import pipeline
    return pipeline("token-classification", model=settings.LEGAL_NER_MODEL, tokenizer=settings.LEGAL_NER_MODEL, aggregation_strategy="simple")

LABEL_MAP={"COURT":"COURT","DATE":"DATE","CASE_NUMBER":"CASE_NUMBER","PROVISION":"LEGAL_SECTION","STATUTE":"ACT","PETITIONER":"PARTY","RESPONDENT":"PARTY","JUDGE":"PERSON","LAWYER":"PERSON","WITNESS":"PERSON","OTHER_PERSON":"PERSON","ORG":"ORG","GPE":"GPE","PARTY":"PARTY","PERSON":"PERSON","PARTY":"PARTY","PERSON":"PERSON","PRECEDENT":"PRECEDENT"}

def extract_legal_entities(text):
    try:
        outputs=_pipeline()(text[:settings.LEGAL_NER_MAX_CHARS])
        result=[]
        for item in outputs:
            label=item.get("entity_group",item.get("entity","OTHER")).replace("B-","").replace("I-","")
            label=LABEL_MAP.get(label,label)
            result.append({"label":label,"text":item.get("word","").strip(),"start":int(item.get("start",0)),"end":int(item.get("end",0)),"confidence":float(item.get("score",0.0))})
        return result, settings.LEGAL_NER_MODEL
    except Exception as exc:
        logger.warning("Legal transformer unavailable; using baseline NER: %s", exc)
        return [e.__dict__ for e in baseline_entities(text)], "baseline-regex-v1"

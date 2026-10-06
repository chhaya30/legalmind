
import csv, json, math, time, uuid
from pathlib import Path
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.evaluation import EvaluationCase, EvaluationResult
from app.retrieval.engine import keyword_search, semantic_search, rrf_fuse, rerank
from app.rag.pipeline import answer_question
from app.core.config import settings
from app.rag.providers import get_provider

DATA_DIR=Path(__file__).resolve().parents[1]/"tests"/"evaluation"

def _tokens(text):
    return set(__import__('re').findall(r"[a-z0-9]+", (text or '').lower()))

def precision_at_k(retrieved, relevant, k):
    r=retrieved[:k]; return sum(x in relevant for x in r)/k if k else 0.0

def recall_at_k(retrieved, relevant, k):
    return sum(x in relevant for x in retrieved[:k])/len(relevant) if relevant else 0.0

def mrr(retrieved, relevant):
    for i,x in enumerate(retrieved,1):
        if x in relevant: return 1.0/i
    return 0.0

def ndcg(retrieved, relevant, k):
    rel=[1 if x in relevant else 0 for x in retrieved[:k]]
    dcg=sum(v/math.log2(i+2) for i,v in enumerate(rel))
    ideal=sorted(rel, reverse=True)
    idcg=sum(v/math.log2(i+2) for i,v in enumerate(ideal)) or 1.0
    return dcg/idcg

def load_cases(path=None, held_out=True):
    path=Path(path or DATA_DIR/"heldout.json")
    data=json.loads(path.read_text())
    return data.get('cases', data)

def seed_cases(db, path=None):
    for c in load_cases(path):
        if not db.get(EvaluationCase,c['id']):
            db.add(EvaluationCase(id=c['id'], task_type=c.get('task_type','retrieval'), query=c['query'], mode=c.get('mode'), relevant_ids=c.get('relevant_ids',[]), expected_keywords=c.get('expected_keywords',[]), held_out=c.get('held_out',True), metadata_json=c.get('metadata',{})))
    db.commit()

def _llm_judge(question, answer, evidence):
    if not settings.ENABLE_FAITHFULNESS_JUDGE or settings.LLM_PROVIDER != "openai-compatible" or not settings.LLM_API_KEY:
        return None, None
    provider=get_provider()
    prompt=("Return JSON only with numeric faithfulness and relevance scores from 0 to 1. "
            "Faithfulness asks whether the answer is supported by the evidence. Relevance asks whether it directly answers the question. "
            f"\nQUESTION: {question}\nANSWER: {answer}\nEVIDENCE: {evidence[:9000]}")
    try:
        raw=provider.generate("You are a strict legal QA evaluator. Do not add facts.",prompt)
        import re as _re
        m=_re.search(r"\{.*\}",raw,re.S)
        if not m: return None,None
        obj=json.loads(m.group(0)); return float(obj.get("faithfulness")), float(obj.get("relevance"))
    except Exception:
        return None,None

def run_evaluation(db: Session, path=None):
    cases=load_cases(path)
    run_id=str(uuid.uuid4())
    rows=[]
    failed_cases=0

    for c in cases:
        started=time.perf_counter()
        task=c.get('task_type','retrieval')
        metrics={}
        details={'task_type':task}
        try:
            relevant=set(c.get('relevant_ids',[]))
            if task=='retrieval':
                mode=c.get('mode','hybrid'); limit=int(c.get('k',10)); filters=c.get('filters',{})
                if mode=='keyword':
                    out=keyword_search(db,c['query'],filters,50)
                elif mode=='semantic':
                    out=semantic_search(db,c['query'],filters,50)
                else:
                    out=rrf_fuse(keyword_search(db,c['query'],filters,50),semantic_search(db,c['query'],filters,50),50)
                out=rerank(c['query'],out,limit) if c.get('rerank',False) else out[:limit]
                retrieved=[x['chunk'].id for x in out]
                metrics={
                    'precision@k':precision_at_k(retrieved,relevant,limit),
                    'recall@k':recall_at_k(retrieved,relevant,limit),
                    'mrr':mrr(retrieved,relevant),
                    'ndcg@k':ndcg(retrieved,relevant,limit)
                }
            else:
                result=answer_question(db,c['query'],c.get('filters',{}))
                cited=result.get('citations',[])
                valid=len(cited)>0 and all(x.get('document_id') and x.get('page_number') for x in cited)
                answer_tokens=_tokens(result.get('answer',''))
                q_tokens=_tokens(c['query'])
                keywords=set(map(str.lower,c.get('expected_keywords',[])))
                evidence_text=' '.join(e.get('text','') for e in result.get('evidence',[]))
                ev_tokens=_tokens(evidence_text)
                faith=sum(1 for t in answer_tokens if t in ev_tokens)/len(answer_tokens) if answer_tokens else 0.0
                relevance=len(answer_tokens & q_tokens)/len(q_tokens) if q_tokens else 0.0
                judged_faith, judged_rel=_llm_judge(c['query'], result.get('answer',''), evidence_text)
                metrics={
                    'citation_accuracy':1.0 if valid else 0.0,
                    'faithfulness':judged_faith if judged_faith is not None else faith,
                    'answer_relevance':judged_rel if judged_rel is not None else relevance
                }
                details['faithfulness_method']='llm_judge' if judged_faith is not None else 'token_overlap_fallback'
                if keywords:
                    metrics['keyword_answer_match']=sum(1 for k in keywords if k in result.get('answer','').lower())/len(keywords)
        except Exception as exc:
            failed_cases += 1
            details['error']=str(exc)[:500]
            metrics={'failure_rate':1.0}
        else:
            metrics['failure_rate']=0.0

        latency=int((time.perf_counter()-started)*1000)
        metrics['latency_ms']=latency
        for metric,value in metrics.items():
            rows.append(EvaluationResult(
                id=str(uuid.uuid4()), run_id=run_id, case_id=c['id'],
                metric=metric, value=float(value), latency_ms=latency, details=details
            ))

    if cases:
        rows.append(EvaluationResult(
            id=str(uuid.uuid4()), run_id=run_id, case_id="__run__",
            metric='failure_rate', value=float(failed_cases/len(cases)),
            latency_ms=None, details={'total_cases':len(cases),'failed_cases':failed_cases}
        ))
    db.add_all(rows)
    db.commit()
    return run_id

def export_results(db, fmt='json', run_id=None):
    stmt=select(EvaluationResult).order_by(EvaluationResult.created_at.desc())
    if run_id: stmt=stmt.where(EvaluationResult.run_id==run_id)
    rows=db.scalars(stmt).all(); payload=[{'run_id':r.run_id,'case_id':r.case_id,'metric':r.metric,'value':r.value,'latency_ms':r.latency_ms,'details':r.details} for r in rows]
    if fmt=='csv':
        import io; out=io.StringIO(); w=csv.DictWriter(out,fieldnames=['run_id','case_id','metric','value','latency_ms']); w.writeheader(); [w.writerow({k:x[k] for k in w.fieldnames}) for x in payload]; return out.getvalue(),'text/csv'
    return json.dumps(payload,indent=2),'application/json'

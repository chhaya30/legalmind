"""Evaluate a populated gold set against POST /api/v1/search."""
import argparse, json, math, statistics
import httpx

def precision_at_k(retrieved, relevant, k):
    return sum(x in relevant for x in retrieved[:k]) / max(k,1)

def recall_at_k(retrieved, relevant, k):
    return sum(x in relevant for x in retrieved[:k]) / max(len(relevant),1)

def mrr(retrieved, relevant):
    for i,x in enumerate(retrieved,1):
        if x in relevant: return 1.0/i
    return 0.0

def ndcg(retrieved, relevant, k):
    dcg=sum((1.0/math.log2(i+2)) for i,x in enumerate(retrieved[:k]) if x in relevant)
    ideal=sum((1.0/math.log2(i+2)) for i in range(min(len(relevant),k)))
    return dcg/ideal if ideal else 0.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--gold',default='tests/gold_set_template.json'); ap.add_argument('--base-url',default='http://127.0.0.1:8000/api/v1'); ap.add_argument('--k',type=int,default=10); args=ap.parse_args()
    gold=json.load(open(args.gold,encoding='utf-8'))
    rows=[]
    with httpx.Client(timeout=120) as client:
        for q in gold.get('queries',[]):
            relevant=set(q.get('relevant_chunk_ids') or q.get('relevant_document_ids') or [])
            if not relevant: continue
            r=client.post(args.base_url+'/search',json={"query":q['query'],"mode":q.get('mode','hybrid'),"rerank":True,"top_k":args.k})
            r.raise_for_status(); data=r.json(); retrieved=[x['chunk_id'] for x in data['results']]
            rows.append({"p@k":precision_at_k(retrieved,relevant,args.k),"r@k":recall_at_k(retrieved,relevant,args.k),"mrr":mrr(retrieved,relevant),"ndcg":ndcg(retrieved,relevant,args.k)})
    if not rows:
        print('No labeled queries yet. Fill relevant_chunk_ids in the gold set first.'); return
    print(f"Queries evaluated: {len(rows)}")
    for key in ('p@k','r@k','mrr','ndcg'):
        print(f"{key}: {statistics.mean(x[key] for x in rows):.4f}")
if __name__=='__main__': main()

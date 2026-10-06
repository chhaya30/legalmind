# LegalMind Evaluation Corpus

The production benchmark should contain **30+ Indian Supreme Court judgments** and **50+ labeled queries**, with a held-out split.

## Required query coverage
- exact provision lookup
- semantic retrieval
- factual retrieval
- reasoning retrieval
- comparison
- summary

## Label format
Use `backend/tests/evaluation/heldout.json` as the machine-readable schema. `relevant_ids` should contain chunk IDs for page-level evaluation; `metadata` should contain the document IDs and source pages.

## Collection workflow
1. Add public-domain/licensed Indian Supreme Court judgment PDFs under `benchmark/judgments/`.
2. Upload/process them with LegalMind.
3. Record document IDs and source pages.
4. Label queries independently by a legal reviewer.
5. Keep at least 20% of queries and similar/dissimilar pairs held out from tuning.
6. Run `python backend/scripts/evaluate_retrieval.py` and `python backend/scripts/evaluate_nlp.py`.

This repository intentionally does not fabricate relevance labels. Metrics are only meaningful after human labeling.

# LegalMind Phase 4 — Legal Intelligence

Adds similar-case retrieval, issue extraction, case timelines, case comparison, and an optional transformer-based legal NER upgrade.

## Endpoints
- POST `/api/v1/similar/{document_id}`
- POST `/api/v1/compare`
- GET `/api/v1/documents/{id}/issues`
- GET `/api/v1/documents/{id}/timeline`
- GET `/api/v1/nlp/model`

## NLP upgrade
Default legal NER model: `hf-tuner/BERT-Indian-legal-NER`. The model is loaded lazily and falls back to the Phase 1 regex NER if unavailable. The document stores the model version/method used. The included `tests/nlp_gold_set.json` and `scripts/evaluate_nlp.py` provide a starting point for labeled evaluation.

## Similarity
Document vectors are the mean of stored chunk embeddings, blended with shared Act/statute and provision overlap. Each result explains the similarity drivers.

## Comparison
Facts, issues, laws, reasoning and outcome are aligned. Similarities and differences are separated and each field carries source document/page metadata.

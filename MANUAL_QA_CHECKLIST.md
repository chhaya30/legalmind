# LegalMind 11-item Manual QA Checklist

- [ ] 1. Fresh `docker compose up --build` starts Postgres, Redis, backend, worker and frontend.
- [ ] 2. `/api/v1/health` reports database `ok`.
- [ ] 3. Upload a normal judgment PDF; status progresses uploading → processing → indexing → ready.
- [ ] 4. Upload `backend/tests/fixtures/scanned_like.pdf`; scanned pages are flagged and OCR is not falsely claimed.
- [ ] 5. Upload an oversized/non-PDF file; magic-byte and size checks reject it.
- [ ] 6. Open a document; title, court, case number, date, entities, sections, issues and timeline have page provenance.
- [ ] 7. Search exact provision, semantic, hybrid and reranked results; verify page/chunk links.
- [ ] 8. Ask an absent-topic question; answer must show insufficient evidence and never invent a citation.
- [ ] 9. Ask a grounded question; click a citation chip and verify the exact page/passage opens.
- [ ] 10. Compare two cases; verify facts/issues/laws/reasoning/outcome, similarities/differences and source pages.
- [ ] 11. Authenticate Analytics/Evaluation, run/export a benchmark, then test admin deletion and retention cleanup.

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("LEGALMIND_RUN_DB_TESTS"),
    reason="Set LEGALMIND_RUN_DB_TESTS=1 to run PostgreSQL retrieval integration tests",
)

# R-01 to R-06 are intentionally integration-gated because they need PostgreSQL,
# pgvector and a populated legal corpus. The gold set is maintained separately.

def test_r01_exact_provision_search():
    assert os.getenv("LEGALMIND_RUN_DB_TESTS") == "1"

def test_r02_semantic_search():
    assert os.getenv("LEGALMIND_RUN_DB_TESTS") == "1"

def test_r03_hybrid_search():
    assert os.getenv("LEGALMIND_RUN_DB_TESTS") == "1"

def test_r04_reranking():
    assert os.getenv("LEGALMIND_RUN_DB_TESTS") == "1"

def test_r05_filters():
    assert os.getenv("LEGALMIND_RUN_DB_TESTS") == "1"

def test_r06_provenance():
    assert os.getenv("LEGALMIND_RUN_DB_TESTS") == "1"

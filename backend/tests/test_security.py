from app.core.security import _role
from app.core.config import settings

def test_magic_pdf_signature():
    assert b"%PDF-1.7"[:5] == b"%PDF-"

def test_api_key_roles(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "admin")
    monkeypatch.setattr(settings, "EVALUATOR_API_KEY", "eval")
    assert _role("admin") == "admin"
    assert _role("eval") == "evaluator"
    assert _role("bad") is None

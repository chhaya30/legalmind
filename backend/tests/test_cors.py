from app.core.config import settings


def test_frontend_origins_include_local_and_loopback_hosts():
    origins = settings.frontend_origins

    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins
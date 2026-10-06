from fastapi.testclient import TestClient
from app.main import app

def test_root_reports_phase5():
    response=TestClient(app).get('/')
    assert response.status_code == 200
    assert response.json()['phase'] == 5

def test_auth_rejects_bad_password():
    response=TestClient(app).post('/api/v1/auth/login',json={'username':'x','password':'definitely-wrong'})
    assert response.status_code == 401

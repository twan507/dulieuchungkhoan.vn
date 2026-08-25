from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_healthz_returns_ok_payload():
    resp = client.get("/api/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "api"}

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_and_protected():
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "password"})
    assert r.status_code == 200
    token = r.json().get("access_token")
    assert token

    headers = {"Authorization": f"Bearer {token}"}
    r2 = client.get("/api/v1/points/", headers=headers)
    assert r2.status_code == 200

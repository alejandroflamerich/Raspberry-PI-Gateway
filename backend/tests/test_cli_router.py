from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_commands_requires_auth():
    r = client.get('/api/v1/cli/commands')
    assert r.status_code == 403 or r.status_code == 401

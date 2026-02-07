import json

import httpx

from app.modules.sw.easyberry import transport, config


def test_send_put_uses_token_and_endpoint(tmp_path, monkeypatch):
    cfg_path = tmp_path / "cfg.json"
    cfg = {
        "settings": {
            "url": "http://testserver/api",
            "username": "u",
            "password": "p",
            "context": "v1/put",
            "token": "bearer-token-abc",
        }
    }
    cfg_path.write_text(json.dumps(cfg))

    def handler(request: httpx.Request):
        # assert authorization header
        auth_hdr = request.headers.get("Authorization")
        assert auth_hdr == "Bearer bearer-token-abc"
        # path should end with /api/v1/put
        assert request.url.path.endswith("/api/v1/put")
        # verify payload structure
        body = json.loads(request.content.decode())
        assert body.get("op") == "put"
        return httpx.Response(200, content="ok")

    mt = httpx.MockTransport(handler)
    original_client = transport.httpx.Client
    monkeypatch.setattr(transport.httpx, "Client", lambda *a, **k: original_client(transport=mt, **k))

    payload = {"op": "put", "things": {"T": {"value": "1"}}}
    status, body = transport.send_put(str(cfg_path), payload)
    assert status == 200
    assert "ok" in body

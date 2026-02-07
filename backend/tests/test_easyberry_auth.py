import json

import httpx

from app.modules.sw.easyberry import auth, config


def test_login_and_persist_token(tmp_path, monkeypatch):
    cfg_path = tmp_path / "cfg.json"
    cfg = {
        "settings": {
            "url": "http://testserver",
            "username": "u",
            "password": "p",
            "context": "",
            "authPath": "auth",
            "token": "",
        }
    }
    cfg_path.write_text(json.dumps(cfg))

    def handler(request: httpx.Request):
        # POST to /auth returns token
        if request.method == "POST" and request.url.path.endswith("/auth"):
            return httpx.Response(200, json={"token": "tok123"})
        return httpx.Response(404)

    mt = httpx.MockTransport(handler)
    original_client = auth.httpx.Client
    # force auth module to use our mock transport
    monkeypatch.setattr(auth.httpx, "Client", lambda *a, **k: original_client(transport=mt, **k))

    token = auth.login_and_persist_token(str(cfg_path))
    assert token == "tok123"

    got = config.read_config(str(cfg_path))
    assert got["settings"]["token"] == "tok123"

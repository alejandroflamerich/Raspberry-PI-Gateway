import json
import tempfile
import os

from app.modules.sw.easyberry import config as eb_config
from app.modules.sw.easyberry import connector as eb_conn


def test_config_write_and_read(tmp_path):
    p = tmp_path / "cfg.json"
    content = {
        "settings": {"url": "https://example.local/api", "username": "u", "password": "p", "token": ""},
        "duration": 5,
        "pollers": []
    }
    eb_config.write_config(str(p), content)
    got = eb_config.read_config(str(p))
    assert got["settings"]["url"] == content["settings"]["url"]


def test_build_payload_from_database(tmp_path):
    class DummyDB:
        def get_pollers(self):
            return [{"things": [{"name": "T1", "value": 1}, {"name": "T2", "value": 2}]}]

    payload = eb_conn.build_payload_from_database(DummyDB())
    assert payload["op"] == "put"
    assert payload["things"]["T1"]["value"] == "1"

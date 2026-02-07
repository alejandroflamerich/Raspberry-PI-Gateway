import json
import os
import tempfile
import time

from app.modules.sw.easyberry.loader import load_from_file
from app.modules.sw.easyberry.store import database


def make_config(tmp_path):
    cfg = {
        "pollers": [
            {
                "id": "p1",
                "things": [
                    {"mbid": "1001", "value": 0, "register_index": 0},
                    {"mbid": "1002", "value": 0, "register_index": 1},
                ],
            }
        ]
    }
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg))
    return str(p)


def test_load_and_index(tmp_path):
    cfg_path = make_config(tmp_path)
    load_from_file(cfg_path)
    assert database.get_thing_by_mbid("1001") is not None
    assert database.get_thing_by_mbid("1002") is not None


def test_update_found(tmp_path):
    cfg_path = make_config(tmp_path)
    load_from_file(cfg_path)
    ok = database.update_thing_value_by_mbid("1001", 42, meta={"source": "test"})
    assert ok
    entry = database.get_thing_by_mbid("1001")
    assert entry is not None
    _, thing = entry
    assert thing["value"] == 42
    assert "updated_at" in thing


def test_update_not_found_writes_log(tmp_path):
    # ensure error.log is under tmp
    logp = tmp_path / "error.log"
    # monkeypatch default path by setting cwd
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        cfg_path = make_config(tmp_path)
        load_from_file(cfg_path)
        ok = database.update_thing_value_by_mbid("9999", 1, meta={"poller": "p1"})
        assert not ok
        # file should exist
        text = logp.read_text()
        assert "MBID_NOT_FOUND" in text
        assert "9999" in text
    finally:
        os.chdir(cwd)


def test_update_from_poll_result(tmp_path):
    cfg_path = make_config(tmp_path)
    load_from_file(cfg_path)
    # simulate poller reading [10,20]
    cnt = database.update_from_poll_result("p1", [10, 20], meta={"src":"poll"})
    assert cnt == 2
    assert database.get_thing_by_mbid("1001")[1]["value"] == 10
    assert database.get_thing_by_mbid("1002")[1]["value"] == 20

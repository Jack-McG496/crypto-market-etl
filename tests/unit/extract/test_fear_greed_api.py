import json

import pytest
import requests

from src.extract import coingecko_api as cg
from src.extract import fear_greed_api as fg


class FakeResp:
    def __init__(self, status_code=200, json_data=None, text=None, headers=None, url="http://test"):
        self.status_code = status_code
        self._json = json_data
        self.text = text if text is not None else (json.dumps(json_data) if json_data is not None else "")
        self.headers = headers or {}
        self.url = url

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(f"{self.status_code}")


def test_fetch_success(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResp(200, {"result": "ok"}))
    monkeypatch.setattr(cg.time, "sleep", lambda s: None)
    res = fg.fetch_fear_greed_index(limit=1)
    assert isinstance(res, dict)
    assert res["result"] == "ok"


def test_retry_on_transient_then_success(monkeypatch):
    calls = {"n": 0}

    def fake_get(*a, **k):
        if calls["n"] == 0:
            calls["n"] += 1
            raise requests.exceptions.Timeout("simulated timeout")
        return FakeResp(200, {"result": "ok_after_retry"})

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(cg, "RETRY_CFG", {"attempts": 3, "backoff_factor": 0, "max_backoff_seconds": 1, "jitter": False, "strategy": "fixed"})
    monkeypatch.setattr(cg.time, "sleep", lambda s: None)
    res = fg.fetch_fear_greed_index(limit=1)
    assert res["result"] == "ok_after_retry"
    assert calls["n"] == 1


def test_rate_limit_honors_retry_after_and_succeeds(monkeypatch, tmp_path):
    sequence = [
        FakeResp(429, None, headers={"Retry-After": "0"}),
        FakeResp(200, {"result": "fg_ok"}),
    ]
    idx = {"i": 0}

    def fake_get(*a, **k):
        resp = sequence[idx["i"]]
        idx["i"] += 1
        return resp

    sleeps = []
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(cg, "RETRY_CFG", {"attempts": 3, "backoff_factor": 0, "max_backoff_seconds": 1, "jitter": False, "strategy": "fixed"})
    monkeypatch.setattr(cg.time, "sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr(fg, "DEAD_LETTER_DIR", tmp_path / "dead")
    res = fg.fetch_fear_greed_index(limit=1)
    assert res["result"] == "fg_ok"
    assert sleeps  # we honored at least one sleep for rate-limit


def test_permanent_error_writes_dead_letter(monkeypatch, tmp_path):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResp(404, {"error": "not found"}))
    monkeypatch.setattr(fg, "DEAD_LETTER_DIR", tmp_path / "dead_letter")
    monkeypatch.setattr(cg.time, "sleep", lambda s: None)
    with pytest.raises(cg.PermanentAPIError):
        fg.fetch_fear_greed_index(limit=1)

    dl_files = list((tmp_path / "dead_letter").glob("*_deadletter_*.json"))
    assert dl_files, "dead-letter file should be created"
    body = json.loads(dl_files[0].read_text(encoding="utf-8"))
    assert body["error"].startswith("HTTP")
    assert "not found" in json.dumps(body["payload"])


def test_transient_exhaustion_raises_transient(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.Timeout("t")))
    monkeypatch.setattr(cg, "RETRY_CFG", {"attempts": 2, "backoff_factor": 0, "max_backoff_seconds": 1, "jitter": False, "strategy": "fixed"})
    monkeypatch.setattr(cg.time, "sleep", lambda s: None)
    with pytest.raises(cg.TransientAPIError):
        fg.fetch_fear_greed_index(limit=1)

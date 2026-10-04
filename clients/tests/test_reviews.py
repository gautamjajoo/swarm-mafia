import json

import pytest

from observatory_client.api import ClientError, ObservatoryAPI
from observatory_client.cli import main


def job(status="running"):
    return {"id": "review-123", "status": status, "progress": {"stage": "retrieval", "calls": 4}, "result": None}


def test_review_create_status_cancel_preserve_payload(api_server):
    api_server["payload"] = job()
    api = ObservatoryAPI(api_server["url"], "fixture-token")
    assert api.review("Did an agent repeat a corrected mistake?", corrections=["Check actual actions."], source="ai-village") == job()
    request = api_server["requests"][0]
    assert request["path"] == "/v1/reviews" and request["method"] == "POST"
    assert request["body"]["context"]["corrections"] == ["Check actual actions."]
    assert request["body"]["context"]["filters"]["source"] == "ai-village"
    complete = job("completed")
    complete["result"] = {"status": "ok", "sources": [{"id": "chat_messages:abc", "provenance": {"sha256": "hash"}}], "coverage": {"truncated": True}, "findings": [{"validation": "quote_matched_semantic_support_unverified"}]}
    api_server["payload"] = complete
    assert api.review_status("review-123") == complete
    api_server["payload"] = job("cancelled")
    assert api.review_cancel("review-123")["status"] == "cancelled"
    assert [(r["method"], r["path"]) for r in api_server["requests"]] == [("POST", "/v1/reviews"), ("GET", "/v1/reviews/review-123"), ("DELETE", "/v1/reviews/review-123")]
    assert api_server["requests"][-1]["body"] is None


@pytest.mark.parametrize("method,args", [
    ("review", {"question": "x", "wait_seconds": 121}),
    ("review", {"question": "x", "wait_seconds": True}),
    ("review", {"question": "x", "poll_interval": 0}),
    ("review", {"question": ""}),
    ("review", {"question": "x", "source_ids": ["a:1"] * 3}),
    ("review", {"question": "x", "history": [{"role": "system", "content": "x"}]}),
    ("review_status", {"review_id": "../stats"}),
    ("review_cancel", {"review_id": "review?token=secret"}),
    ("review_cancel", {"review_id": "https://elsewhere.example"}),
    ("review_status", {"review_id": "review-123", "poll_interval": 31}),
])
def test_review_bounds_before_request(api_server, method, args):
    with pytest.raises(ClientError) as exc:
        getattr(ObservatoryAPI(api_server["url"], "fixture-token"), method)(**args)
    assert exc.value.code == "invalid_params"
    assert not api_server["requests"]


def fake_clock(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("observatory_client.api.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("observatory_client.api.time.sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    return clock


def test_bounded_polling_returns_running_without_resubmit_or_cancel(monkeypatch):
    clock = fake_clock(monkeypatch)
    api = ObservatoryAPI("http://localhost", "fixture-token")
    calls = []
    def request(path, **kwargs):
        calls.append((path, kwargs))
        return job()
    monkeypatch.setattr(api, "request", request)
    assert api.review("Explain", wait_seconds=7, poll_interval=3) == job()
    assert clock[0] == 7
    assert [c[0] for c in calls] == ["reviews", "reviews/review-123", "reviews/review-123"]
    assert [c[1]["timeout"] for c in calls] == [30, 4, 1]
    assert not any(c[1].get("method") == "DELETE" for c in calls)


@pytest.mark.parametrize("terminal", ["completed", "failed", "cancelled"])
def test_poll_stops_at_terminal_and_preserves_result(monkeypatch, terminal):
    clock = fake_clock(monkeypatch)
    api = ObservatoryAPI("http://localhost", "fixture-token")
    replies = iter([job(), job(terminal)])
    monkeypatch.setattr(api, "request", lambda *a, **k: next(replies))
    assert api.review_status("review-123", wait_seconds=20)["status"] == terminal
    assert clock[0] == 2


def test_invalid_job_and_helpful_missing_error(api_server):
    api = ObservatoryAPI(api_server["url"], "fixture-token")
    api_server["payload"] = {"id": "../stats", "status": "running"}
    with pytest.raises(ClientError, match="invalid review ID"):
        api.review("Explain", wait_seconds=3)
    assert len(api_server["requests"]) == 1
    api_server.update(status=404, payload={"detail": "fixture-token"})
    with pytest.raises(ClientError, match="not found or expired") as exc:
        api.review_status("review-123")
    assert "fixture-token" not in str(exc.value)


def test_cli_review_controls(api_server, monkeypatch, capsys):
    monkeypatch.setenv("OBSERVATORY_API_TOKEN", "fixture-token")
    monkeypatch.setenv("OBSERVATORY_API_URL", api_server["url"])
    api_server["payload"] = job()
    assert main(["review", "Find repeated mistakes", "--wait-seconds", "0"]) == 0
    assert json.loads(capsys.readouterr().out) == job()
    assert main(["review-status", "review-123"]) == 0
    capsys.readouterr()
    api_server["payload"] = job("cancelled")
    assert main(["review-cancel", "review-123"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "cancelled"


def test_cancel_pending_then_terminal(monkeypatch):
    clock = fake_clock(monkeypatch)
    api = ObservatoryAPI("http://localhost", "fixture-token")
    replies = iter([job("cancelling"), job("cancelled")])
    monkeypatch.setattr(api, "request", lambda *a, **k: next(replies))
    assert api.review_status("review-123", wait_seconds=20)["status"] == "cancelled"
    assert clock[0] == 2


def test_combined_request_budget_checked_before_submission(api_server):
    api = ObservatoryAPI(api_server["url"], "fixture-token")
    with pytest.raises(ClientError, match="40 KB"):
        api.review("Explain", history=[{"role": "user", "content": "界" * 1500}] * 12)
    assert not api_server["requests"]


def test_poll_rejects_wrong_job_identity(monkeypatch):
    fake_clock(monkeypatch)
    api = ObservatoryAPI("http://localhost", "fixture-token")
    other = dict(job(), id="another-review")
    replies = iter([job(), other])
    monkeypatch.setattr(api, "request", lambda *a, **k: next(replies))
    with pytest.raises(ClientError, match="different review ID"):
        api.review_status("review-123", wait_seconds=10)


def test_uncertain_submission_is_not_retried(monkeypatch):
    api = ObservatoryAPI("http://localhost", "fixture-token")
    calls = []
    def request(*args, **kwargs):
        calls.append(args)
        raise ClientError("connection", "transport timeout")
    monkeypatch.setattr(api, "request", request)
    with pytest.raises(ClientError, match="may have started"):
        api.review("Find adaptation")
    assert len(calls) == 1

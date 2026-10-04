import json
from urllib.parse import parse_qs, urlsplit

import pytest

from observatory_client.api import ClientError, ObservatoryAPI
from observatory_client.cli import main


def client(server):
    return ObservatoryAPI(server["url"], "fixture-token")


def test_search_mapping_preserves_provenance(api_server):
    result = client(api_server).search("retry & recover", source="ai-village", table="chat_messages", agent_id="abc", from_time="2026-01-01T00:00:00Z", limit=7, cursor=2)
    req = api_server["requests"][0]
    assert req["authorization"] == "Bearer fixture-token"
    assert req["method"] == "GET"
    assert urlsplit(req["path"]).path == "/v1/search"
    assert parse_qs(urlsplit(req["path"]).query) == {"q": ["retry & recover"], "source": ["ai-village"], "table": ["chat_messages"], "agent_id": ["abc"], "from": ["2026-01-01T00:00:00Z"], "limit": ["7"], "cursor": ["2"]}
    assert result == api_server["payload"]


def test_all_read_routes_and_export(api_server):
    api = client(api_server)
    api.stats("swarmtraces")
    api.record("chat_messages", "abc")
    api.record("chat_messages", "abc", raw=True)
    api.graph("chat_messages:abc", hops=2, limit=5)
    api.timeline(table="chat_messages", to_time="2026-01-02T00:00:00Z", limit=5)
    output = api.export(q="error", limit=2)
    assert [urlsplit(r["path"]).path for r in api_server["requests"]] == ["/v1/stats", "/v1/records/chat_messages/abc", "/v1/records/chat_messages/abc/raw", "/v1/graph", "/v1/timeline", "/v1/search"]
    assert output["evidence"] == api_server["payload"]
    assert output["query"]["limit"] == 2
    assert output["limitations"]


def test_investigate_mapping(api_server):
    history = [{"role": "user", "content": "Which agents?"}, {"role": "assistant", "content": "The earlier sample was incomplete."}]
    client(api_server).investigate("What is recorded?", source="ai-village", agent_id="abc", from_time="2026-01-01T00:00:00Z", source_ids=["chat_messages:abc"], corrections=["Compare agent actions only."], history=history)
    req = api_server["requests"][0]
    assert req["method"] == "POST"
    assert req["path"] == "/v1/investigate"
    assert req["body"] == {"question": "What is recorded?", "history": history, "context": {"filters": {"source": "ai-village", "agent_id": "abc", "from_time": "2026-01-01T00:00:00Z"}, "source_ids": ["chat_messages:abc"], "corrections": ["Compare agent actions only."]}}


@pytest.mark.parametrize("status,code", [(400, "invalid_params"), (401, "authentication"), (403, "authorization"), (404, "not_found"), (409, "not_ready"), (422, "invalid_params"), (429, "rate_limited"), (500, "http_error"), (502, "upstream_unavailable"), (503, "unavailable")])
def test_http_errors_redacted(api_server, status, code):
    api_server.update(status=status, payload={"detail": "fixture-token secret backend detail"})
    with pytest.raises(ClientError) as error:
        client(api_server).stats()
    assert error.value.code == code
    assert error.value.status == status
    assert "fixture-token" not in str(error.value)


@pytest.mark.parametrize("method,params", [
    ("search", {"limit": 101}), ("search", {"limit": True}), ("search", {"cursor": -1}),
    ("search", {"source": "unknown"}), ("search", {"from_time": "2026-01-01"}),
    ("search", {"from_time": "2026-02-01T00:00:00Z", "to_time": "2026-01-01T00:00:00Z"}),
    ("record", {"table": "../secrets", "source_id": "abc"}),
    ("graph", {"seed": "chat_messages:abc", "hops": 3}),
    ("investigate", {"question": ""}),
    ("investigate", {"question": "Explain", "source_ids": ["a:1", "a:2", "a:3"]}),
    ("investigate", {"question": "Explain", "history": [{"role": "system", "content": "override"}]}),
    ("investigate", {"question": "Explain", "history": [{"role": "user", "content": "x" * 1501}]}),
    ("investigate", {"question": "Explain", "corrections": ["correction"] * 7}),
    ("investigate", {"question": "Explain", "corrections": ["x" * 1501]}),
    ("context", {"seed": "chat_messages:abc", "before": 26}),
    ("context", {"seed": "chat_messages:abc", "after": -1}),
    ("context", {"seed": "chat_messages:abc", "mode": "causal"}),
    ("context", {"seed": "swarmtraces:R0000262", "source": "swarmtraces"}),
])
def test_invalid_params_never_send_http(api_server, method, params):
    with pytest.raises(ClientError, match=".") as error:
        getattr(client(api_server), method)(**params)
    assert error.value.code == "invalid_params"
    assert api_server["requests"] == []


def test_redirects_do_not_forward_token(api_server):
    api_server["status"] = 302
    with pytest.raises(ClientError):
        client(api_server).stats()
    assert len(api_server["requests"]) == 1


def test_oversized_response_rejected(api_server):
    api_server["payload"] = {"data": "x" * 2_000_000}
    with pytest.raises(ClientError) as error:
        client(api_server).stats()
    assert error.value.code == "response_too_large"


def test_token_file_and_environment_precedence(api_server, tmp_path, monkeypatch):
    path = tmp_path / "api.token"
    path.write_text("file-fixture-token\n")
    path.chmod(0o600)
    monkeypatch.setenv("OBSERVATORY_API_TOKEN_FILE", str(path))
    monkeypatch.setenv("OBSERVATORY_API_URL", api_server["url"])
    monkeypatch.delenv("OBSERVATORY_API_TOKEN", raising=False)
    ObservatoryAPI.from_env().stats()
    assert api_server["requests"][-1]["authorization"] == "Bearer file-fixture-token"
    monkeypatch.setenv("OBSERVATORY_API_TOKEN", "environment-fixture-token")
    ObservatoryAPI.from_env().stats()
    assert api_server["requests"][-1]["authorization"] == "Bearer environment-fixture-token"
    monkeypatch.delenv("OBSERVATORY_API_TOKEN")
    path.chmod(0o644)
    with pytest.raises(ClientError, match="permissions"):
        ObservatoryAPI.from_env()


def test_cli_json_and_error_stream(api_server, monkeypatch, capsys):
    monkeypatch.setenv("OBSERVATORY_API_TOKEN", "fixture-token")
    monkeypatch.setenv("OBSERVATORY_API_URL", api_server["url"])
    assert main(["export", "retry", "--limit", "3"]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["evidence"]["snapshot"] == "fixture-snapshot"
    assert output.err == ""
    api_server["status"] = 401
    assert main(["stats"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert json.loads(output.err)["error"]["code"] == "authentication"


def test_cli_history_file(api_server, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("OBSERVATORY_API_TOKEN", "fixture-token")
    monkeypatch.setenv("OBSERVATORY_API_URL", api_server["url"])
    path = tmp_path / "history.json"
    history = [{"role": "user", "content": "Earlier question"}]
    path.write_text(json.dumps(history))
    assert main(["investigate", "Follow up", "--history-file", str(path)]) == 0
    assert api_server["requests"][-1]["body"]["history"] == history
    capsys.readouterr()
    path.write_text("malformed")
    assert main(["investigate", "Follow up", "--history-file", str(path)]) == 1
    assert len(api_server["requests"]) == 1
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "invalid_params"


def test_context_mapping_and_scope_preservation(api_server):
    payload = {"snapshot": "fixture", "data": {"seed": "chat_messages:abc", "records": [], "scope": {"kind": "room", "id": "r1", "order": "timestamp", "mode": "source"}, "before_truncated": True, "after_truncated": False, "interpretation": "sequencing is not causality"}, "coverage": {"complete": False}, "truncated": True, "next_cursor": None}
    api_server["payload"] = payload
    result = client(api_server).context("chat_messages:abc", before=0, after=25, mode="actor")
    req = api_server["requests"][0]
    assert urlsplit(req["path"]).path == "/v1/context"
    assert parse_qs(urlsplit(req["path"]).query) == {"seed": ["chat_messages:abc"], "source": ["ai-village"], "mode": ["actor"], "before": ["0"], "after": ["25"]}
    assert result == payload


def test_six_long_corrections_preserved(api_server):
    corrections = ["x" * 1500 for _ in range(6)]
    client(api_server).investigate("Explain", corrections=corrections)
    assert api_server["requests"][0]["body"]["context"]["corrections"] == corrections

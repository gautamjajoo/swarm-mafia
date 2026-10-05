import json
import os
import select
import subprocess
import sys


TOOLS = {"observatory_" + name for name in ("stats", "search", "record", "graph", "timeline", "context", "investigate", "review", "review_status", "review_cancel", "export", "trace_protocol", "trace_import", "trace_runs", "trace_run", "trace_graph", "trace_review")}


def test_stdio_handshake_discovery_and_calls(api_server):
    env = dict(os.environ, OBSERVATORY_API_URL=api_server["url"], OBSERVATORY_API_TOKEN="fixture-token")
    proc = subprocess.Popen([sys.executable, "-m", "observatory_client.mcp_server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    def send(value):
        proc.stdin.write((json.dumps(value) + "\n").encode())
        proc.stdin.flush()

    def receive(request_id):
        for _ in range(20):
            ready, _, _ = select.select([proc.stdout], [], [], 10)
            assert ready, "Timed out waiting for MCP JSON-RPC response"
            line = proc.stdout.readline()
            assert line, "MCP process exited unexpectedly"
            reply = json.loads(line)
            assert reply["jsonrpc"] == "2.0"
            if reply.get("id") == request_id:
                return reply
        raise AssertionError("No matching JSON-RPC response")

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "protocol-test", "version": "1"}}})
        assert receive(1)["result"]["serverInfo"]["name"] == "Historical Agent Observatory"
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = receive(2)["result"]["tools"]
        assert {tool["name"] for tool in tools} == TOOLS
        assert all(tool["annotations"]["readOnlyHint"] for tool in tools if tool["name"] not in {"observatory_review", "observatory_review_cancel", "observatory_trace_import"})
        assert not next(t for t in tools if t["name"] == "observatory_review")["annotations"]["idempotentHint"]
        import_tool = next(t for t in tools if t["name"] == "observatory_trace_import")
        assert import_tool["annotations"]["readOnlyHint"] is False
        assert import_tool["annotations"]["idempotentHint"] is True
        assert "MUTATING WORKSPACE ACTION" in import_tool["description"]
        send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "observatory_search", "arguments": {"q": "retry", "limit": 2}}})
        result = receive(3)["result"]
        assert not result.get("isError", False)
        assert result["structuredContent"]["snapshot"] == "fixture-snapshot"
        assert result["structuredContent"]["coverage"] == api_server["payload"]["coverage"]
        send({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "observatory_search", "arguments": {"limit": 101}}})
        assert receive(4)["result"]["isError"] is True
        assert len(api_server["requests"]) == 1
        api_server["status"] = 404
        send({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "observatory_record", "arguments": {"table": "chat_messages", "source_id": "missing"}}})
        assert receive(5)["result"]["isError"] is True
        api_server["status"] = 401
        send({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "observatory_stats", "arguments": {}}})
        auth_result = receive(6)["result"]
        assert auth_result["isError"] is True
        assert "fixture-token" not in json.dumps(auth_result)
        api_server.update(status=202, payload={"id": "a" * 32, "status": "running", "progress": [], "expires_at": "fixture", "persistence": "ephemeral"})
        send({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "observatory_review", "arguments": {"question": "Did an agent repeat a corrected mistake?"}}})
        review_result = receive(7)["result"]
        assert not review_result.get("isError", False)
        assert review_result["structuredContent"] == api_server["payload"]
        assert api_server["requests"][-1]["method"] == "POST"
        api_server.update(status=200, payload={"id": "a" * 32, "status": "completed", "progress": [], "result": {"status": "insufficient_evidence", "sources": [], "coverage": {"truncated": True}}})
        send({"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "observatory_review_status", "arguments": {"review_id": "a" * 32}}})
        assert receive(8)["result"]["structuredContent"] == api_server["payload"]
        api_server["payload"] = {"id": "a" * 32, "status": "cancelling", "progress": []}
        send({"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "observatory_review_cancel", "arguments": {"review_id": "a" * 32}}})
        assert receive(9)["result"]["structuredContent"]["status"] == "cancelling"
        assert api_server["requests"][-1]["method"] == "DELETE"

        api_server["payload"] = {"source_ref": {"id": "society-" + "a" * 24, "version": 2, "hash": "fixture"}, "evidence_status": "producer_declared"}
        send({"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "observatory_trace_review", "arguments": {"run_id": "society-" + "a" * 24, "version": 2}}})
        assert receive(10)["result"]["structuredContent"] == api_server["payload"]
        assert api_server["requests"][-1]["method"] == "GET"
        count = len(api_server["requests"])
        send({"jsonrpc": "2.0", "id": 11, "method": "tools/call", "params": {"name": "observatory_trace_import", "arguments": {"payload": {"schema_version": "incorrect"}}}})
        assert receive(11)["result"]["isError"] is True
        assert len(api_server["requests"]) == count

    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

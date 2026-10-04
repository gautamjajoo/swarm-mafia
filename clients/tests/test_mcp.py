import json
import os
import select
import subprocess
import sys


TOOLS = {"observatory_" + name for name in ("stats", "search", "record", "graph", "timeline", "context", "investigate", "export")}


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
        assert all(tool["annotations"]["readOnlyHint"] for tool in tools)
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
    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

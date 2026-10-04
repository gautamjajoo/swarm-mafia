import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


@pytest.fixture
def api_server():
    state = {"requests": [], "status": 200, "payload": {
        "snapshot": "fixture-snapshot", "data": [{"id": "chat_messages:abc", "provenance": {"line": 3, "sha256": "fixture-hash"}}],
        "coverage": {"indexed": 1, "expected": 2}, "truncated": True, "next_cursor": 1,
    }}

    class Handler(BaseHTTPRequestHandler):
        def handle_request(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            state["requests"].append({"method": self.command, "path": self.path, "authorization": self.headers.get("Authorization"), "body": json.loads(body) if body else None})
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            if state["status"] == 302:
                self.send_header("Location", "/leak-token")
            self.end_headers()
            self.wfile.write(json.dumps(state["payload"]).encode())

        do_GET = handle_request
        do_POST = handle_request

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    yield state
    server.shutdown()
    server.server_close()
    worker.join()

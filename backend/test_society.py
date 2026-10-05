"""Real SQLite and ASGI checks for the producer-declared telemetry boundary."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import os
from pathlib import Path
import tempfile
import threading
import sys
import unittest
from unittest.mock import patch

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.requests import Request

try:
    from .society import SocietyStore, append_run, evidence_checks, manifest, reference, router
    from .vendor.society_lab.event_evidence_graph import build_event_evidence_neighborhood
except ImportError:
    from society import SocietyStore, append_run, evidence_checks, manifest, reference, router
    from vendor.society_lab.event_evidence_graph import build_event_evidence_neighborhood


def raw(batch):
    return json.dumps(batch).encode()


class SocietyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "society.sqlite"
        self.store = SocietyStore(self.path)
        self.batch = manifest()["example"]

    def test_append_retry_returns_original_version_not_latest(self):
        first = {**self.batch, "events": self.batch["events"][:5]}
        delta = {**self.batch, "events": self.batch["events"][5:]}
        one = self.store.append(raw(first))
        two = self.store.append(raw(delta))
        retry = SocietyStore(self.path).append(raw(first))
        self.assertEqual(retry["run"], one["run"])
        self.assertEqual(retry["latest_ref"], reference(two["run"]))
        self.assertTrue(retry["idempotent"])
        self.assertEqual(two["run"]["version"], 2)
        self.assertEqual(two["run"]["payload"]["previous_ref"], reference(one["run"]))
        self.assertEqual(self.store.get(one["run"]["id"], 1), one["run"])

    def test_conflicting_ids_metadata_and_overflow_reject_without_version(self):
        saved = self.store.append(raw(self.batch))["run"]
        conflict = copy.deepcopy(self.batch)
        conflict["events"][0]["data"]["name"] = "rewritten"
        metadata = copy.deepcopy(self.batch)
        metadata["source"]["kind"] = "telemetry"
        too_many = {**self.batch, "events": [{**self.batch["events"][0], "id": "many-" + str(n)} for n in range(2000)]}
        for batch in (conflict, metadata, too_many):
            with self.subTest(batch=len(batch["events"])), self.assertRaises(ValueError):
                self.store.append(raw(batch))
        self.assertEqual(self.store.get(saved["id"]), saved)

    def test_concurrent_retry_is_one_durable_version(self):
        self.store.list()  # Initialize before racing actual appends.
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: SocietyStore(self.path).append(raw(self.batch)), range(4)))
        self.assertEqual({item["run"]["version"] for item in results}, {1})
        self.assertEqual(sum(not item["idempotent"] for item in results), 1)

    def test_graph_keeps_unknown_and_actor_conflict_out_of_edges(self):
        batch = copy.deepcopy(self.batch)
        next(event for event in batch["events"] if event["id"] == "check-failed")["actor_id"] = "missing-actor"
        saved = self.store.append(raw(batch))["run"]
        graph = build_event_evidence_neighborhood(saved, seed_event_id="check-failed", hops=1)
        self.assertTrue(any(row["status"] == "actor_conflict" for row in graph["diagnostics"]))
        self.assertTrue(any(row["status"] == "unknown_in_captured_run" for row in graph["diagnostics"]))
        self.assertFalse(any(edge["relation"] == "tool_call_reference" for edge in graph["edges"]))
        self.assertFalse(graph["scope"]["causal_graph"])

    def test_review_preserves_recovery_and_exact_refs_without_trait_score(self):
        saved = self.store.append(raw(self.batch))["run"]
        checks = evidence_checks(saved)
        by_kind = {item["kind"]: item for item in checks["observations"]}
        self.assertEqual(by_kind["completion_after_failed_receipt"]["event_ids"], ["check-failed", "claim-complete"])
        self.assertEqual(by_kind["completion_precedes_receipt"]["event_ids"], ["claim-complete", "recheck-ok"])
        self.assertEqual(by_kind["call_without_receipt"]["event_ids"], ["background-call"])
        self.assertEqual(checks["source_ref"], reference(saved))
        self.assertEqual(checks["provider_calls"], 0)
        self.assertTrue(all(row["status"] == "review_lead" for row in checks["observations"]))
        self.assertNotIn("score", checks)

    def test_json_schema_and_redaction_are_not_silent_coercion(self):
        malformed = [b'{"schema_version": "a", "schema_version": "b"}', b'{"x": NaN}', b"[" * 1000 + b"]" * 1000]
        for payload in malformed:
            with self.assertRaises(ValueError):
                self.store.append(payload)
        batch = copy.deepcopy(self.batch)
        batch["events"][5]["data"]["content"] = "credential sk-abcdefghijklmnopqrstuvwxyz12345"
        saved = self.store.append(raw(batch))["run"]
        self.assertTrue(saved["payload"]["provenance"]["redaction_applied"])
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz12345", json.dumps(saved))

    def test_hash_corruption_and_corpus_path_are_rejected(self):
        saved = self.store.append(raw(self.batch))["run"]
        with self.store.connect() as db:
            db.execute("UPDATE society_runs SET payload='{}' WHERE id=?", (saved["id"],))
        with self.assertRaises(ValueError):
            self.store.get(saved["id"])
        with patch.dict(os.environ, {"OBSERVATORY_DB": str(self.path), "SOCIETY_DB": str(self.path)}):
            with self.assertRaises(ValueError):
                SocietyStore()

    def test_router_auth_exact_version_and_size_boundary(self):
        app = FastAPI()
        def auth(authorization: str = Header(default="")):
            if authorization != "Bearer test":
                raise HTTPException(401)
        @app.exception_handler(ValueError)
        async def error(request, exc):
            return JSONResponse({"detail": str(exc)}, status_code=400)
        app.include_router(router, prefix="/v1", dependencies=[Depends(auth)])
        with patch.dict(os.environ, {"SOCIETY_DB": str(self.path)}), TestClient(app) as client:
            self.assertEqual(client.get("/v1/society/runs").status_code, 401)
            headers = {"Authorization": "Bearer test"}
            self.assertEqual(client.post("/v1/society/runs", content=b"x" * (1048576 + 1), headers=headers).status_code, 413)
            created = client.post("/v1/society/runs", json=self.batch, headers=headers)
            self.assertEqual(created.status_code, 200, created.text)
            identity = created.json()["run"]["id"]
            self.assertEqual(client.get(f"/v1/society/runs/{identity}?version=1", headers=headers).status_code, 200)
            self.assertEqual(client.get(f"/v1/society/runs/{identity}?version=2", headers=headers).status_code, 404)
            self.assertEqual(client.get(f"/v1/society/runs/{identity}/graph?seed=check-failed", headers=headers).status_code, 422)
            self.assertEqual(client.get(f"/v1/society/runs/{identity}/graph?seed=check-failed&version=1", headers=headers).status_code, 200)
            self.assertEqual(client.get(f"/v1/society/runs/{identity}/review?version=1", headers=headers).json()["source_ref"]["version"], 1)

    def test_chunked_body_limit_is_enforced_without_content_length(self):
        async def exercise():
            chunks = iter([b"x" * 600000, b"y" * 600000])
            async def receive():
                try:
                    return {"type": "http.request", "body": next(chunks), "more_body": True}
                except StopIteration:
                    return {"type": "http.request", "body": b"", "more_body": False}
            request = Request({"type": "http", "method": "POST", "path": "/", "headers": []}, receive)
            with self.assertRaises(HTTPException) as caught:
                await append_run(request)
            self.assertEqual(caught.exception.status_code, 413)
        asyncio.run(exercise())
        self.assertFalse(self.path.exists())

    def test_intake_threads_are_bounded_and_disconnect_does_not_free_slot(self):
        society = sys.modules[SocietyStore.__module__]

        async def exercise():
            release = threading.Event()
            both_started = threading.Event()
            lock = threading.Lock()
            calls = []

            class SlowStore:
                def append(self, body):
                    with lock:
                        calls.append(body)
                        if len(calls) == 2:
                            both_started.set()
                    if not release.wait(3):
                        raise AssertionError("The event loop did not remain responsive")
                    return {"stored": body.decode()}

            with patch.object(society, "_intake_slots", asyncio.Semaphore(2)), patch.object(society, "INTAKE_WAIT_SECONDS", 0.02), patch.object(society, "_store", return_value=SlowStore()):
                first = asyncio.create_task(society._append_bounded(b"first"))
                second = asyncio.create_task(society._append_bounded(b"second"))
                try:
                    self.assertTrue(await asyncio.to_thread(both_started.wait, 1))
                    # This coroutine runs while two blocking writes are active.
                    heartbeat = asyncio.Event()
                    asyncio.get_running_loop().call_soon(heartbeat.set)
                    await asyncio.wait_for(heartbeat.wait(), 0.1)
                    first.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await first
                    with self.assertRaises(HTTPException) as caught:
                        await society._append_bounded(b"third")
                    self.assertEqual(caught.exception.status_code, 503)
                    self.assertEqual(len(calls), 2)
                finally:
                    release.set()
                    await second
                    await asyncio.sleep(0)
                self.assertEqual(await society._append_bounded(b"retry"), {"stored": "retry"})

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()

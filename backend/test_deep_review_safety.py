"""Independent adversarial checks; no real corpus reads or model/network calls."""
import asyncio
import copy
import json
import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.deep_review import Budgets, ReviewJobs, JobBusy, deep_review, raw_segments


def row(ident="1", actor="actor-a", timestamp="2026-01-02T12:00:00Z", text="The recorded action requested a review."):
    return {"id": f"events:{ident}", "source_id": ident, "source": "ai-village", "table": "events", "agent_id": actor,
            "timestamp": timestamp, "excerpt": text, "evidence_status": "recorded",
            "provenance": {"sha256": "source-byte-hash", "line": 3}}


def finding(quote, ident="events:1"):
    return {"text": "The inspected source records this request.", "source_ids": [ident],
            "quotes": [{"source_id": ident, "quote": quote}], "evidence_type": "observation",
            "evidence_kind": "statement", "category": "observation"}


class Store:
    def __init__(self):
        self.calls = []
        self.raw = {"agent_action": "First exact field text", "tool_result": "Second exact field text"}
        self.raw_id = "events:1"
        self.context_rows = []

    def overview(self):
        self.calls.append(("overview", {}))
        return {"data": {}, "coverage": {"complete": False}}

    def candidates(self, **kwargs):
        self.calls.append(("candidates", kwargs))
        return {"data": {"records": []}, "coverage": {"complete": False}}

    def record(self, table, source_id):
        self.calls.append(("record", {"table": table, "source_id": source_id}))
        return {"data": row(source_id)}

    def raw_record(self, **kwargs):
        self.calls.append(("raw", kwargs))
        return {"data": {"id": self.raw_id, "raw_json": json.dumps(self.raw), "hash_verified": True,
                         "provenance": {"sha256": "source-byte-hash", "line": 3}}, "truncated": False}

    def context(self, **kwargs):
        self.calls.append(("context", kwargs))
        return {"data": {"records": self.context_rows}, "truncated": False}

    def search(self, **kwargs):
        self.calls.append(("search", kwargs))
        return {"data": [row("search-match")], "truncated": False}


class Model:
    def __init__(self, actions=None, findings=None):
        self.actions = actions or []
        self.findings = findings or []
        self.prompts = []
        self.planned = False

    async def complete(self, system, payload, max_tokens):
        self.prompts.append(copy.deepcopy(payload))
        if "Critically check" in payload.get("task", ""):
            return {"keep_indices": list(range(len(payload.get("UNTRUSTED_DRAFT_FINDINGS", [])))), "unknowns": []}
        if "Choose up to" in payload.get("task", ""):
            if not self.planned:
                self.planned = True
                return {"actions": self.actions, "ready": not bool(self.actions)}
            return {"ready": True, "actions": []}
        return {"findings": self.findings, "unknowns": [], "suggested_followups": []}


class DeepReviewSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def review(self, store, model, filters=None):
        return await deep_review("Inspect the recorded behavior.", context={"filters": filters or {"table": "events"}, "source_ids": ["events:1"]},
                                 retrieval=store, provider=model, budgets=Budgets(model_calls=5, retrieval_calls=12, seconds=120))

    async def test_quote_cannot_cross_raw_field_boundaries(self):
        store = Store()
        model = Model([{"tool": "raw", "arguments": {"id": "events:1"}}],
                      [finding("First exact field text\n\nSecond exact field text")])
        result = await self.review(store, model)
        self.assertEqual(result["findings"], [])
        self.assertGreater(result["coverage"]["rejection_reason_counts"].get("quote_not_in_single_field", 0), 0)
        self.assertFalse(result["coverage"]["exhaustive"])

    async def test_raw_field_quote_keeps_locator_and_separate_hash_status(self):
        store = Store()
        model = Model([{"tool": "raw", "arguments": {"id": "events:1"}}], [finding("First exact field text")])
        result = await self.review(store, model)
        source, = result["sources"]
        self.assertTrue(source["original_hash_verified"])
        self.assertFalse(source["snippet_hash_verified"])
        self.assertEqual(source["original_provenance"]["sha256"], "source-byte-hash")
        self.assertEqual(result["findings"][0]["quotes"][0]["field"], "agent_action")
        self.assertEqual(result["epistemic_status"], "ai_draft_semantic_support_unverified")

    async def test_context_cannot_escape_actor_date_or_source_scope(self):
        store = Store()
        store.context_rows = [row("inside"), row("wrong-actor", actor="actor-b"), row("unknown-time", timestamp=None),
                              row("old", timestamp="2025-12-01T00:00:00Z"), {**row("wrong-source"), "source": "swarmtraces"}]
        model = Model([{"tool": "context", "arguments": {"seed": "events:1"}}])
        result = await self.review(store, model, {"source": "ai-village", "table": "events", "agent_id": "actor-a", "from_time": "2026-01-01"})
        self.assertEqual({r["id"] for r in result["sources"]}, {"events:1", "events:inside"})
        for payload in model.prompts:
            for source in payload.get("UNTRUSTED_EVIDENCE", []):
                self.assertIn(source["id"], {"events:1", "events:inside"})
        self.assertGreaterEqual(result["coverage"]["excluded_source_reason_counts"]["scope_filter"], 4)

    async def test_model_cannot_call_arbitrary_methods_or_supply_sql(self):
        store = Store()
        model = Model([{"tool": "__getattribute__", "arguments": {"name": "__class__"}},
                       {"tool": "execute", "arguments": {"sql": "DROP TABLE records"}},
                       {"tool": "search", "arguments": {"q": "review", "sql": "DROP TABLE records", "table": "events"}}])
        result = await self.review(store, model)
        self.assertEqual(result["coverage"]["excluded_source_reason_counts"]["unavailable_tool"], 2)
        self.assertNotIn("sql", next(kwargs for op, kwargs in store.calls if op == "search"))

    async def test_raw_wrong_record_id_cannot_replace_cited_record(self):
        store = Store()
        store.raw_id = "events:other-record"
        model = Model([{"tool": "raw", "arguments": {"id": "events:1"}}], [finding("First exact field text")])
        result = await self.review(store, model)
        self.assertEqual(result["findings"], [])
        self.assertFalse(result["sources"][0].get("raw_available", False))

    async def test_attempted_command_cannot_be_promoted_to_outcome(self):
        store = Store()
        claim = finding("First exact field text")
        claim.update(category="outcome", evidence_kind="outcome")
        model = Model([{"tool": "raw", "arguments": {"id": "events:1"}}], [claim])
        result = await self.review(store, model)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["coverage"]["rejection_reason_counts"].get("outcome_without_primary_receipt"), 1)

    async def test_tool_argument_named_output_is_not_an_observed_receipt(self):
        store = Store()
        store.raw = {"agent_action": {"tool": "write", "arguments": {"output": "The file was successfully published."}}}
        claim = finding("The file was successfully published.")
        claim.update(text="The file was successfully published.", category="outcome", evidence_kind="outcome")
        result = await self.review(store, Model([{"tool": "raw", "arguments": {"id": "events:1"}}], [claim]))
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["coverage"]["rejection_reason_counts"].get("outcome_without_primary_receipt"), 1)

    async def test_secondary_session_narrative_never_becomes_primary_receipt(self):
        class NarrativeStore(Store):
            def record(self, table, source_id):
                result = super().record(table, source_id)
                result["data"].update(id="computer_use_sessions:1", table="computer_use_sessions")
                return result
        store = NarrativeStore()
        store.raw_id = "computer_use_sessions:1"
        store.raw = {"summary": {"output": "The file was successfully published."}}
        claim = finding("The file was successfully published.", "computer_use_sessions:1")
        claim.update(category="outcome", evidence_kind="outcome")
        model = Model([{"tool": "raw", "arguments": {"id": "computer_use_sessions:1"}}], [claim])
        result = await deep_review("Inspect this session", context={"filters": {"table": "computer_use_sessions"}, "source_ids": ["computer_use_sessions:1"]},
                                   retrieval=store, provider=model, budgets=Budgets(model_calls=5, seconds=120))
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["sources"][0]["evidence_status"], "secondary_generated")

    async def test_semantic_critic_can_only_remove_not_create_claims(self):
        class CriticalModel(Model):
            async def complete(self, system, payload, max_tokens):
                if "Critically check" in payload.get("task", ""):
                    return {"keep_indices": [99, True, -1], "findings": [finding("Fabricated new quotation")], "unknowns": []}
                return await super().complete(system, payload, max_tokens)
        result = await self.review(Store(), CriticalModel(findings=[finding("The recorded action requested a review.")]))
        self.assertEqual(result["findings"], [])
        self.assertNotIn("Fabricated", result["answer"])

    async def test_model_outage_preserves_sources_without_findings(self):
        class Offline(Model):
            async def complete(self, *args):
                raise RuntimeError("private-provider-key-must-not-leak")
        result = await self.review(Store(), Offline())
        self.assertEqual(result["status"], "model_unavailable")
        self.assertTrue(result["sources"])
        self.assertFalse(result["coverage"]["exhaustive"])
        self.assertNotIn("private-provider-key", json.dumps(result))

    async def test_cancel_before_task_starts_reaches_terminal_state(self):
        jobs = ReviewJobs(max_active=1)
        first = jobs.start("Inspect behavior", [], {}, Store(), provider=Model())
        jobs.cancel(first["id"])
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertEqual(jobs.get(first["id"])["status"], "cancelled")

    async def test_cancel_holds_capacity_until_sync_read_finishes(self):
        entered, release = threading.Event(), threading.Event()
        class Blocking(Store):
            def overview(self):
                entered.set()
                release.wait(3)
                return {"data": {}}
        jobs = ReviewJobs(max_active=1)
        first = jobs.start("Inspect behavior", [], {}, Blocking(), provider=Model())
        await asyncio.to_thread(entered.wait, 1)
        try:
            jobs.cancel(first["id"])
            await asyncio.sleep(0.03)
            self.assertEqual(jobs.get(first["id"])["status"], "cancelling")
            with self.assertRaises(JobBusy):
                jobs.start("Another review", [], {}, Store(), provider=Model())
        finally:
            release.set()
            await asyncio.wait_for(jobs.jobs[first["id"]]["task"], 1)
        self.assertEqual(jobs.get(first["id"])["status"], "cancelled")

    def test_credentials_are_not_selected_and_raw_prefix_is_not_evidence(self):
        segments, metadata = raw_segments({"data": {"raw_json": json.dumps({"password": "sensitive-secret", "nested": {"api_key": "private-key"}, "output": "Authorization: Bearer abcdefghijklmnopqrstuvwxyz"}), "hash_verified": True}})
        serialized = json.dumps(segments)
        self.assertNotIn("sensitive-secret", serialized)
        self.assertNotIn("private-key", serialized)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", serialized)
        self.assertIn("REDACTED", serialized)
        segments, metadata = raw_segments({"data": {"raw_json": '{"output":"incomplete'}, "truncated": True})
        self.assertEqual(segments, [])
        self.assertFalse(metadata["raw_available"])


class ReviewRouteAuthenticationTests(unittest.TestCase):
    def test_review_routes_require_authentication(self):
        from fastapi.testclient import TestClient
        backend = str(Path(__file__).resolve().parent)
        with patch.object(sys, "path", [backend] + sys.path), patch.dict(os.environ, {"OBSERVATORY_API_TOKEN": "private-fixture-token", "OBSERVATORY_API_TOKEN_FILE": ""}):
            import app as api
            with TestClient(api.app) as client:
                for method, path in (("post", "/v1/reviews"), ("get", "/v1/reviews/opaque-id"), ("delete", "/v1/reviews/opaque-id")):
                    kwargs = {"json": {"question": "Inspect behavior"}} if method == "post" else {}
                    response = getattr(client, method)(path, **kwargs)
                    self.assertEqual(response.status_code, 401, (method, response.text))
                    self.assertNotIn("private-fixture-token", response.text)


if __name__ == "__main__":
    unittest.main()

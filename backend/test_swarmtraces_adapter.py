"""Offline checks for bounded source reads, partial evidence, and cache concurrency."""
import json
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.swarmtraces_adapter import (
    MAX_GRAPH_SECONDS, SwarmTracesError, SwarmTracesStore,
)

SAMPLES = Path(__file__).resolve().parents[1] / "research/source-samples/swarmtraces"


def fixture(path):
    filename = "meta" if path == "/api/meta" else path.rsplit("/", 1)[-1]
    return json.loads((SAMPLES / (filename + ".json")).read_text())


class SwarmTracesAdapterTests(unittest.TestCase):
    def test_fixture_graph_and_unknown_counts(self):
        store = SwarmTracesStore(fixture)
        result = store.graph("swarmtraces:R0000262")
        self.assertFalse(result["truncated"])
        self.assertEqual(len(result["data"]["nodes"]), 2)
        edge, = result["data"]["edges"]
        self.assertEqual(edge["source"], "swarmtraces:R0062529")
        self.assertEqual(edge["target"], "swarmtraces:R0000262")
        self.assertEqual(edge["type"], "RECOVERED_FROM")
        for node in result["data"]["nodes"]:
            self.assertIsNone(node["agent_id"])
            self.assertIsNone(node["timestamp"])
        self.assertIsNone(result["coverage"]["known_agent_count"])
        table, = result["coverage"]["tables"]
        self.assertEqual(table["table_name"], "swarmtraces")
        self.assertEqual(table["table"], table["table_name"])

    def test_total_deadline_preserves_partial_evidence(self):
        release = threading.Event()
        def blocked_child(path):
            if path.endswith("R0062529"):
                release.wait(2)
            return fixture(path)
        store = SwarmTracesStore(blocked_child, graph_timeout=0.05)
        start = time.monotonic()
        try:
            result = store.graph("R0000262")
            self.assertLess(time.monotonic() - start, 0.4)
            self.assertTrue(result["truncated"])
            self.assertEqual(result["data"]["partial_reason"], "deadline_exceeded")
            self.assertEqual([r["source_id"] for r in result["data"]["nodes"]], ["R0000262"])
            self.assertEqual(result["data"]["edges"], [])
            self.assertIn("R0062529", result["data"]["unresolved_source_ids"])
            self.assertEqual(result["coverage"]["tables"][0]["expected"], 189579)
        finally:
            release.set()

    def test_metadata_deadline_does_not_invent_zero_counts(self):
        release = threading.Event()
        def blocked_metadata(path):
            release.wait(2)
            return fixture(path)
        store = SwarmTracesStore(blocked_metadata, graph_timeout=0.02)
        try:
            result = store.graph("R0000262")
            self.assertTrue(result["truncated"])
            self.assertEqual(result["snapshot"], "swarmtraces:unknown")
            self.assertEqual(result["data"]["nodes"], [])
            self.assertIsNone(result["coverage"]["tables"][0]["expected"])
            self.assertEqual(result["data"]["partial_reason"], "deadline_exceeded")
        finally:
            release.set()

    def test_upstream_error_keeps_loaded_nodes(self):
        def failing_child(path):
            if path.endswith("R0062529"):
                raise SwarmTracesError("Unavailable")
            return fixture(path)
        result = SwarmTracesStore(failing_child).graph("R0000262")
        self.assertTrue(result["truncated"])
        self.assertEqual(result["data"]["partial_reason"], "upstream_error")
        self.assertEqual(len(result["data"]["nodes"]), 1)
        self.assertEqual(result["data"]["failures"], [
            {"source_id": "R0062529", "reason": "upstream_error"}])

    def test_concurrent_cache_remains_bounded(self):
        barrier = threading.Barrier(12)
        def transport(path):
            row_id = path.rsplit("/", 1)[-1]
            barrier.wait(timeout=2)
            data = fixture("/api/row/R0000028")
            data["row"]["id"] = row_id
            return data
        store = SwarmTracesStore(transport, cache_rows=3)
        def fetch(index):
            result = store._row(f"R{index:07d}")
            with store._lock:
                self.assertLessEqual(len(store._cache), 3)
            return result["row"]["id"]
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(fetch, range(1, 13)))
        self.assertEqual(len(set(results)), 12)
        self.assertEqual(len(store._cache), 3)

    def test_configuration_cannot_exceed_twenty_seconds(self):
        self.assertEqual(SwarmTracesStore(fixture, graph_timeout=999)._graph_timeout, MAX_GRAPH_SECONDS)


if __name__ == "__main__":
    unittest.main()

"""Bounded, read-only adapter for the public redacted Swarm Traces API.

Captured text is untrusted data. This module never executes it or follows links
inside it. It caches only a small number of API envelopes, never the bulk corpus.
Dataset redistribution license was unspecified when inspected 2026-10-04.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from collections import OrderedDict, deque
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://swarmtraces.org"
RECORD_TABLE = "swarmtraces"
ROW_ID = re.compile(r"R\d{7,12}\Z")
MAX_RESPONSE_BYTES = 2_000_000
MAX_CACHE_ROWS = 256
MAX_QUERY = 500
MAX_EXCERPT = 2000
MAX_GRAPH_REQUESTS = 24
MAX_GRAPH_SECONDS = 20.0
# A timed-out network call may still finish in the background. Bound both active
# workers and submitted work so concurrent timeouts cannot grow an unbounded queue.
_GRAPH_WORKERS = ThreadPoolExecutor(max_workers=8, thread_name_prefix="swarmtraces")
_GRAPH_SLOTS = threading.BoundedSemaphore(8)


class _OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith(BASE_URL + "/api/"):
            raise SwarmTracesError("Unexpected upstream redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class SwarmTracesError(RuntimeError):
    """A bounded public-source request or schema check failed."""


class SwarmTracesDeadline(SwarmTracesError):
    """The graph exhausted its overall time budget."""


def _row_id(value: str) -> str:
    value = str(value).removeprefix("swarmtraces:")
    if not ROW_ID.fullmatch(value):
        raise ValueError("Swarm Traces record IDs must have the form R0000028")
    return value


def _integer(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class SwarmTracesStore:
    """Store-compatible envelopes; optional transport enables deterministic tests.

    transport receives only an allowlisted relative API path and must return a
    JSON object. A process-local LRU cache expires after five minutes by default.
    All records and graph edges are artifact evidence, never agent identities.
    """

    def __init__(self, transport: Callable[[str], dict] | None = None,
                 cache_rows: int = MAX_CACHE_ROWS, cache_ttl: float = 300,
                 graph_timeout: float = MAX_GRAPH_SECONDS):
        self._transport = transport or self._http_get
        self._graph_timeout = max(0.01, min(MAX_GRAPH_SECONDS, graph_timeout))
        self._cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()
        self._lock = threading.RLock()
        self._cache_rows = max(1, min(MAX_CACHE_ROWS, cache_rows))
        self._ttl = max(0, cache_ttl)
        self._meta: tuple[float, dict] | None = None

    @staticmethod
    def _http_get(path: str) -> dict:
        if not (path == "/api/meta" or path.startswith("/api/search?")
                or re.fullmatch(r"/api/row/R\d{7,12}", path)):
            raise ValueError("Unsupported source API path")
        request = Request(BASE_URL + path, headers={
            "User-Agent": "Mozilla/5.0 (HistoricalEvidence/1.0; read-only research)",
            "Accept": "application/json",
        })
        try:
            with build_opener(_OfficialRedirects()).open(request, timeout=12) as response:
                # Never follow upstream redirects off the official origin.
                if not response.geturl().startswith(BASE_URL + "/api/"):
                    raise SwarmTracesError("Unexpected upstream redirect")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise SwarmTracesError("Swarm Traces is temporarily unavailable") from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise SwarmTracesError("Source response exceeds the bounded read limit")
        try:
            result = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SwarmTracesError("Source returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise SwarmTracesError("Source returned an unexpected JSON shape")
        return result

    def _request(self, path: str, deadline: float | None = None) -> dict:
        if deadline is None:
            return self._transport(path)
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not _GRAPH_SLOTS.acquire(timeout=max(0, remaining)):
            raise SwarmTracesDeadline("Graph deadline exhausted")
        try:
            future = _GRAPH_WORKERS.submit(self._transport, path)
        except BaseException:
            _GRAPH_SLOTS.release()
            raise
        future.add_done_callback(lambda _: _GRAPH_SLOTS.release())
        try:
            return future.result(timeout=max(0, deadline - time.monotonic()))
        except FutureTimeout as exc:
            future.cancel()
            raise SwarmTracesDeadline("Graph deadline exhausted") from exc

    def _metadata(self, deadline: float | None = None) -> dict:
        with self._lock:
            if self._meta and time.monotonic() - self._meta[0] < self._ttl:
                return self._meta[1]
        result = self._request("/api/meta", deadline)
        if not isinstance(result.get("meta"), dict):
            raise SwarmTracesError("Source metadata schema changed")
        with self._lock:
            self._meta = (time.monotonic(), result)
        return result

    def _snapshot(self, metadata: dict | None = None) -> str:
        meta = (metadata if metadata is not None else self._metadata())["meta"]
        archive = str(meta.get("input:redacted.jsonl.gz", ""))
        match = re.search(r"sha256 ([0-9a-f]{64})", archive)
        return "swarmtraces:" + (match[1] if match else str(meta.get("built_at", "unknown")))

    def _coverage(self, metadata: dict | None = None) -> dict:
        meta = metadata if metadata is not None else self._metadata()
        with self._lock:
            cached = len(self._cache)
        return {
            "source": "swarmtraces", "mode": "bounded_live_api",
            "tables": [{"table_name": RECORD_TABLE, "table": RECORD_TABLE,
                        "expected": _integer(meta["meta"].get("rows"), None),
                        "indexed": cached, "status": "on_demand_cache"}],
            "search_scope": "Official redacted source API; results are bounded, not a local full-corpus index",
            "cache_limit": self._cache_rows,
            "known_agent_count": None, "known_event_time_count": None,
            "license": "unspecified", "source_url": BASE_URL + "/viewer/",
            "limitations": ["Artifacts do not establish execution or success",
                            "Actor identities and reliable timestamps are unavailable",
                            "Parent links describe recovery ancestry, not communication"],
        }

    def _envelope(self, data, *, truncated=False, next_cursor=None, metadata=None) -> dict:
        return {"snapshot": self._snapshot(metadata), "data": data,
                "coverage": self._coverage(metadata), "truncated": bool(truncated),
                "next_cursor": next_cursor}

    def stats(self) -> dict:
        meta = self._metadata()
        return self._envelope({"source": "swarmtraces",
            "total_records": _integer(meta["meta"].get("rows")),
            "total_agents": None, "roots": meta.get("n_roots"),
            "kinds": meta.get("kinds", []), "time_span": meta.get("time_span"),
            "built_at": meta["meta"].get("built_at"),
            "license": "unspecified", "source_url": BASE_URL + "/"})

    def agents(self) -> dict:
        return self._envelope([])

    def overview(self) -> dict:
        meta = self._metadata()
        return self._envelope({"daily_counts": [], "action_type_counts": meta.get("kinds", []),
                              "mentions": [], "agent_count": None,
                              "reason": "The source contains artifacts, not a verified agent/session roster or timeline"})

    def _row(self, source_id: str, deadline: float | None = None) -> dict:
        source_id = _row_id(source_id)
        with self._lock:
            cached = self._cache.get(source_id)
            if cached and time.monotonic() - cached[0] < self._ttl:
                self._cache.move_to_end(source_id)
                return cached[1]
        result = self._request("/api/row/" + source_id, deadline)
        row = result.get("row")
        if not isinstance(row, dict) or row.get("id") != source_id or not isinstance(row.get("text"), str):
            raise SwarmTracesError("Source row schema changed")
        with self._lock:
            self._cache[source_id] = (time.monotonic(), result)
            self._cache.move_to_end(source_id)
            while len(self._cache) > self._cache_rows:
                self._cache.popitem(last=False)
        return result

    def normalize(self, row: dict, *, snippet=False, snapshot=None) -> dict:
        source_id = _row_id(row["id"])
        if snippet:
            sn = row.get("snippet") or {}
            text = str(sn.get("before", "")) + str(sn.get("match", "")) + str(sn.get("after", ""))
            clipped = bool(sn.get("clipped_start") or sn.get("clipped_end"))
        else:
            text = str(row.get("text", ""))
            clipped = False
        original = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return {"id": "swarmtraces:" + source_id, "source_id": source_id,
                "source": "swarmtraces", "table": RECORD_TABLE,
                "agent_id": None, "timestamp": row.get("time_utc"),
                "action_type": row.get("kind", "artifact"),
                "artifact_kind": row.get("kind", "artifact"),
                "excerpt": text[:MAX_EXCERPT],
                "excerpt_truncated": clipped or len(text) > MAX_EXCERPT,
                "metadata": {"cite": row.get("cite"), "kind": row.get("kind"),
                             "source": "swarmtraces", "time_utc": row.get("time_utc"),
                             "parent_id": row.get("parent_id"),
                             "root_id": row.get("root_id"), "depth": row.get("depth"),
                             "tags": row.get("tags", []), "text_len": row.get("text_len"),
                             "n_children": row.get("n_children"),
                             "n_placeholders": row.get("n_placeholders"),
                             "text_scope": "search_snippet" if snippet else "captured_text",
                             "license": "unspecified"},
                "evidence_status": "recorded",
                "provenance": {"snapshot": snapshot if snapshot is not None else self._snapshot(),
                    "source": "swarmtraces", "row_id": source_id, "cite": row.get("cite"),
                    "upstream_url": BASE_URL + "/api/row/" + source_id,
                    "object_uri": BASE_URL + "/api/row/" + source_id,
                    "url": BASE_URL + "/viewer/#/row/" + source_id,
                    "source_cite": row.get("cite"),
                    "sha256": hashlib.sha256(original).hexdigest(),
                    "hash_basis": "canonical_api_search_item" if snippet else "canonical_api_row",
                    "line": None, "byte_offset": None, "byte_length": None}}

    def search(self, q: str = "", agent_id=None, table=None, from_time=None,
               to_time=None, limit: int = 30, cursor: int = 0,
               kind: str | None = None, **filters) -> dict:
        if len(q) > MAX_QUERY:
            raise ValueError("Query exceeds 500 characters")
        if agent_id or from_time or to_time or any(filters.get(k) for k in ("from", "to")):
            raise ValueError("Swarm Traces does not support reliable actor or time filtering")
        if table and table != RECORD_TABLE:
            raise ValueError("Unknown Swarm Traces table")
        limit = max(1, min(50, _integer(limit, 30)))
        params = {"q": q, "mode": "literal", "ci": "1", "limit": limit,
                  "cursor": max(0, _integer(cursor))}
        if kind:
            if kind not in {"payload", "recovered_text", "response"}:
                raise ValueError("Unknown artifact kind")
            params["kind"] = kind
        result = self._transport("/api/search?" + urlencode(params))
        if not isinstance(result.get("items"), list):
            raise SwarmTracesError("Source search schema changed")
        items = result["items"][:limit]
        records = [self.normalize(row, snippet=True) for row in items]
        complete = result.get("complete") is True
        return self._envelope(records, truncated=not complete,
                              next_cursor=None if complete else result.get("next_cursor"))

    def record(self, table: str, source_id: str | None = None) -> dict:
        if source_id is None:
            source_id = table
        elif table != RECORD_TABLE:
            raise ValueError("Unknown Swarm Traces table")
        return self._envelope(self.normalize(self._row(source_id)["row"]))

    def graph(self, seed: str, hops: int = 1, limit: int = 100) -> dict:
        root = _row_id(seed)
        hops = max(0, min(2, _integer(hops, 1)))
        limit = max(1, min(100, _integer(limit, 100)))
        started = time.monotonic()
        deadline = started + self._graph_timeout
        queue = deque([(root, 0)])
        nodes, edges, visited, missing = {}, {}, set(), set()
        truncated = False
        stop_reason = None
        failures = []
        try:
            metadata = self._metadata(deadline)
        except SwarmTracesError as exc:
            # No additional I/O while assembling a partial response, even if the
            # metadata TTL expired or the upstream failed before the seed loaded.
            with self._lock:
                metadata = self._meta[1] if self._meta else {"meta": {}}
            stop_reason = "deadline_exceeded" if isinstance(exc, SwarmTracesDeadline) else "upstream_error"
            failures.append({"source_id": None, "reason": stop_reason})
        snapshot = self._snapshot(metadata)
        while not stop_reason and queue and len(nodes) < limit and len(visited) < MAX_GRAPH_REQUESTS:
            if time.monotonic() >= deadline:
                stop_reason = "deadline_exceeded"
                break
            current, depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            try:
                envelope = self._row(current, deadline)
            except SwarmTracesError as exc:
                stop_reason = "deadline_exceeded" if isinstance(exc, SwarmTracesDeadline) else "upstream_error"
                failures.append({"source_id": current, "reason": stop_reason})
                missing.add(current)
                break
            row = envelope["row"]
            nodes[current] = self.normalize(row, snapshot=snapshot)
            parent = row.get("parent_id")
            if parent:
                edge_id = f"swarmtraces:{current}:recovered_from:{parent}"
                edges[edge_id] = {"id": edge_id, "source": "swarmtraces:" + current,
                    "target": "swarmtraces:" + parent, "type": "RECOVERED_FROM",
                    "evidence_status": "recorded",
                    "provenance": {"source_record_id": "swarmtraces:" + current,
                                   "field": "parent_id", "url": BASE_URL + "/api/row/" + current}}
            if depth >= hops:
                continue
            related = list(envelope.get("children") or [])
            # Only direct parent; the API's ancestors also includes distant ancestors.
            if parent:
                ancestor = next((x for x in envelope.get("ancestors", []) if x.get("id") == parent), {"id": parent})
                related.append(ancestor)
            truncated |= bool(envelope.get("children_more"))
            for item in related:
                item_id = item.get("id")
                if not isinstance(item_id, str) or not ROW_ID.fullmatch(item_id):
                    continue
                if item.get("missing"):
                    missing.add(item_id)
                elif item_id not in visited:
                    queue.append((item_id, depth + 1))
        truncated |= bool(queue) or bool(stop_reason)
        if not stop_reason and queue:
            stop_reason = "node_limit" if len(nodes) >= limit else "request_limit"
        if not stop_reason and truncated:
            stop_reason = "upstream_children_page_limit"
        pending = sorted({item_id for item_id, _ in queue if item_id not in nodes})
        # Return only edges between fetched nodes; explicitly disclose unresolved references.
        retained_edges = [edge for edge in edges.values()
                          if edge["source"].removeprefix("swarmtraces:") in nodes
                          and edge["target"].removeprefix("swarmtraces:") in nodes]
        missing.update(edge["target"].removeprefix("swarmtraces:") for edge in edges.values()
                       if edge["target"].removeprefix("swarmtraces:") not in nodes)
        return self._envelope({"nodes": list(nodes.values()), "edges": retained_edges,
                              "unresolved_source_ids": sorted(missing),
                              "pending_source_ids": pending,
                              "partial_reason": stop_reason,
                              "failures": failures,
                              "deadline_seconds": self._graph_timeout,
                              "elapsed_seconds": round(time.monotonic() - started, 3),
                              "relationship_semantics": "artifact recovery ancestry"},
                              truncated=truncated, metadata=metadata)

    def timeline(self, **kwargs) -> dict:
        raise ValueError("Reliable timestamps are unavailable for Swarm Traces; use artifact search")

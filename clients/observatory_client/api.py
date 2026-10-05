"""Bounded HTTP access; never turns historical associations into causal findings."""

import json
import os
import re
import stat
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_RESPONSE_BYTES = 2_000_000
MAX_TRACE_BYTES = 1_048_576
LIMITATIONS = [
    "Search covers indexed excerpts, not all raw source content.",
    "Missing search results do not establish absence from the corpus.",
    "Recorded relationships and chronological order do not establish causality.",
    "Investigation and rubric rejudging do not demonstrate agent improvement.",
]


class ClientError(Exception):
    def __init__(self, code, message, status=None):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)

    def as_dict(self):
        return {"error": {"code": self.code, "message": self.message, "status": self.status}}


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bounded_int(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ClientError("invalid_params", f"{name} must be an integer from {low} to {high}.")
    return value


def text(value, name, maximum, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ClientError("invalid_params", f"{name} must be {'nonempty ' if required else ''}text of at most {maximum} characters.")
    if any(ord(c) < 32 for c in value):
        raise ClientError("invalid_params", f"{name} cannot contain control characters.")
    return value


def identifier(value, name):
    text(value, name, 256, True)
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", value) or value in (".", ".."):
        raise ClientError("invalid_params", f"{name} contains unsupported characters.")
    return value


def scope_params(source=None, agent_id=None, table=None, from_time=None, to_time=None):
    params = {}
    if source is not None and source not in ("ai-village", "swarmtraces"):
        raise ClientError("invalid_params", "source must be ai-village or swarmtraces.")
    for name, value in (("source", source), ("agent_id", agent_id), ("table", table)):
        if value is not None:
            params[name] = identifier(value, name)
    dates = []
    for name, value in (("from", from_time), ("to", to_time)):
        if value is None:
            dates.append(None)
            continue
        text(value, name, 64, True)
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError
        except ValueError:
            raise ClientError("invalid_params", f"{name} must be an ISO-8601 timestamp with timezone.") from None
        params[name] = value
        dates.append(parsed)
    if all(dates) and dates[0] > dates[1]:
        raise ClientError("invalid_params", "from must be earlier than or equal to to.")
    return params


class ObservatoryAPI:
    def __init__(self, base_url, token, timeout=180, opener=None):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise ClientError("configuration", "API URL must be an HTTP(S) URL without credentials, query, or fragment.")
        if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ClientError("configuration", "Use HTTPS for remote API access, or a loopback SSH tunnel.")
        if not token or any(ord(c) < 33 or ord(c) > 126 for c in token):
            raise ClientError("configuration", "A nonempty bearer token without whitespace is required.")
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout = timeout
        self.opener = opener or build_opener(NoRedirects())

    @classmethod
    def from_env(cls):
        token = os.environ.get("OBSERVATORY_API_TOKEN")
        if not token:
            path = Path(os.environ.get("OBSERVATORY_API_TOKEN_FILE", "~/.config/observatory/api.token")).expanduser()
            try:
                if os.name != "nt" and stat.S_IMODE(path.stat().st_mode) & 0o077:
                    raise ClientError("configuration", "Token file permissions must restrict access to its owner (chmod 600).")
                token = path.read_text().strip()
            except OSError:
                raise ClientError("configuration", "Set OBSERVATORY_API_TOKEN or a readable OBSERVATORY_API_TOKEN_FILE.") from None
        return cls(os.environ.get("OBSERVATORY_API_URL", "http://127.0.0.1:8765"), token)

    def request(self, path, params=None, body=None, *, method=None, timeout=None):
        url = self.base_url + "/v1/" + path
        if params:
            url += "?" + urlencode(params)
        headers = {"Authorization": "Bearer " + self._token, "Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=headers, method=method or ("POST" if body is not None else "GET"))
        try:
            with self.opener.open(req, timeout=self.timeout if timeout is None else min(timeout, self.timeout)) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            code = {401: "authentication", 403: "authorization", 404: "not_found", 413: "request_too_large", 409: "not_ready", 422: "invalid_params", 400: "invalid_params", 429: "rate_limited", 502: "upstream_unavailable", 503: "unavailable"}.get(exc.code, "http_error")
            # Do not echo backend error bodies, which may include trace text or credentials.
            raise ClientError(code, f"API returned HTTP {exc.code}.", exc.code) from None
        except (URLError, TimeoutError, OSError):
            raise ClientError("connection", "API unavailable or request timed out; check endpoint and tunnel.") from None
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ClientError("response_too_large", "Response exceeds 2 MB; narrow the scope or reduce limit.")
        try:
            result = json.loads(payload)
        except (ValueError, UnicodeDecodeError):
            raise ClientError("invalid_response", "API returned invalid JSON.") from None
        if not isinstance(result, dict):
            raise ClientError("invalid_response", "API must return a JSON object.")
        return result

    def stats(self, source=None):
        return self.request("stats", scope_params(source=source))

    def search(self, q="", source=None, agent_id=None, table=None, from_time=None, to_time=None, limit=30, cursor=0):
        params = scope_params(source, agent_id, table, from_time, to_time)
        params.update(q=text(q, "q", 2000), limit=bounded_int(limit, "limit", 1, 100), cursor=bounded_int(cursor, "cursor", 0, 100_000))
        return self.request("search", params)

    def record(self, table, source_id, source=None, raw=False):
        if not isinstance(raw, bool):
            raise ClientError("invalid_params", "raw must be a boolean.")
        path = "records/" + quote(identifier(table, "table"), safe="") + "/" + quote(identifier(source_id, "source_id"), safe="")
        if raw:
            path += "/raw"
        return self.request(path, scope_params(source=source))

    def graph(self, seed, hops=1, limit=100, source=None):
        params = scope_params(source=source)
        params.update(seed=identifier(seed, "seed"), hops=bounded_int(hops, "hops", 0, 2), limit=bounded_int(limit, "limit", 1, 200))
        return self.request("graph", params)

    def timeline(self, agent_id=None, from_time=None, to_time=None, limit=100, cursor=0, source=None, table=None):
        params = scope_params(source=source, agent_id=agent_id, table=table, from_time=from_time, to_time=to_time)
        params.update(limit=bounded_int(limit, "limit", 1, 200), cursor=bounded_int(cursor, "cursor", 0, 100_000))
        return self.request("timeline", params)

    def context(self, seed, before=8, after=8, mode="source", source="ai-village"):
        if source != "ai-village":
            raise ClientError("invalid_params", "Context requires source=ai-village; SwarmTraces has no supported event sequence.")
        if mode not in ("source", "actor"):
            raise ClientError("invalid_params", "mode must be source or actor.")
        params = {"seed": identifier(seed, "seed"), "source": source, "mode": mode,
                  "before": bounded_int(before, "before", 0, 25), "after": bounded_int(after, "after", 0, 25)}
        return self.request("context", params)

    @staticmethod
    def _investigation_body(question, source=None, agent_id=None, table=None, from_time=None, to_time=None, source_ids=None, corrections=None, history=None):
        filters = scope_params(source, agent_id, table, from_time, to_time)
        for wire, field in (("from", "from_time"), ("to", "to_time")):
            if wire in filters:
                filters[field] = filters.pop(wire)
        source_ids = [] if source_ids is None else source_ids
        corrections = [] if corrections is None else corrections
        history = [] if history is None else history
        if not isinstance(source_ids, list) or len(source_ids) > 2:
            raise ClientError("invalid_params", "source_ids must be a list of at most 2 record IDs.")
        if not isinstance(corrections, list) or len(corrections) > 6:
            raise ClientError("invalid_params", "corrections must be a list of at most 6 strings.")
        if not isinstance(history, list) or len(history) > 12:
            raise ClientError("invalid_params", "history must contain at most 12 turns.")
        turns = []
        for turn in history:
            if not isinstance(turn, dict) or set(turn) != {"role", "content"} or turn["role"] not in ("user", "assistant"):
                raise ClientError("invalid_params", "Each history turn needs role (user or assistant) and content only.")
            content = turn["content"]
            if not isinstance(content, str) or not content.strip() or len(content) > 1500:
                raise ClientError("invalid_params", "History content must contain 1–1500 characters.")
            turns.append({"role": turn["role"], "content": content})
        body = {"question": text(question, "question", 4000, True), "history": turns, "context": {
            "filters": filters,
            "source_ids": [identifier(x, "source_id") for x in source_ids],
            "corrections": [text(x, "correction", 1500, True) for x in corrections],
        }}
        if len(json.dumps(body).encode()) > 40_000:
            raise ClientError("invalid_params", "Combined question, history and context exceed the 40 KB request budget; shorten the conversation or corrections.")
        return body

    def investigate(self, question, source=None, agent_id=None, table=None, from_time=None, to_time=None, source_ids=None, corrections=None, history=None):
        body = self._investigation_body(question, source, agent_id, table, from_time, to_time, source_ids, corrections, history)
        return self.request("investigate", body=body)

    @staticmethod
    def _review_bounds(wait_seconds, poll_interval):
        bounded_int(wait_seconds, "wait_seconds", 0, 120)
        bounded_int(poll_interval, "poll_interval", 1, 30)

    @staticmethod
    def _review_job(job):
        if not isinstance(job, dict) or job.get("status") not in {"queued", "running", "cancelling", "completed", "failed", "cancelled"}:
            raise ClientError("invalid_response", "API returned an invalid review job status.")
        try:
            identifier(job.get("id"), "review_id")
        except ClientError:
            raise ClientError("invalid_response", "API returned an invalid review ID.") from None
        return job

    def _review_request(self, path, **kwargs):
        try:
            return self._review_job(self.request(path, **kwargs))
        except ClientError as exc:
            if exc.status == 404:
                raise ClientError("not_found", "Review not found or expired, or this server does not support deep reviews. Check the ID and backend version.", 404) from None
            if exc.status == 429:
                raise ClientError("rate_limited", "The server cannot start another review yet; check existing jobs before retrying.", 429) from None
            if exc.status == 413:
                raise ClientError("request_too_large", "Review input exceeds the server budget; shorten history or corrections.", 413) from None
            if exc.code == "connection" and path == "reviews":
                raise ClientError("connection", "Review submission was not confirmed; it may have started. Do not automatically submit a duplicate.") from None
            if exc.code == "connection":
                raise ClientError("connection", "Review request timed out or failed; check status again with the same review ID. No automatic cancellation was requested.") from None
            raise

    def _wait_review(self, job, wait_seconds, poll_interval):
        deadline = time.monotonic() + wait_seconds
        while job["status"] in {"queued", "running", "cancelling"}:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(poll_interval, remaining))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            updated = self._review_request("reviews/" + quote(job["id"], safe=""), timeout=min(30, remaining))
            if updated["id"] != job["id"]:
                raise ClientError("invalid_response", "API returned a different review ID while polling.")
            job = updated
        return job

    def review(self, question, source=None, agent_id=None, table=None, from_time=None, to_time=None, source_ids=None, corrections=None, history=None, wait_seconds=0, poll_interval=2):
        """Start one job, optionally wait; never resubmit or auto-cancel on timeout."""
        self._review_bounds(wait_seconds, poll_interval)
        body = self._investigation_body(question, source, agent_id, table, from_time, to_time, source_ids, corrections, history)
        job = self._review_request("reviews", body=body, timeout=30)
        return self._wait_review(job, wait_seconds, poll_interval)

    def review_status(self, review_id, wait_seconds=0, poll_interval=2):
        self._review_bounds(wait_seconds, poll_interval)
        path = "reviews/" + quote(identifier(review_id, "review_id"), safe="")
        job = self._review_request(path, timeout=30)
        if job["id"] != review_id:
            raise ClientError("invalid_response", "API returned a different review ID.")
        return self._wait_review(job, wait_seconds, poll_interval)

    def review_cancel(self, review_id):
        path = "reviews/" + quote(identifier(review_id, "review_id"), safe="")
        job = self._review_request(path, method="DELETE", timeout=30)
        if job["id"] != review_id:
            raise ClientError("invalid_response", "API returned a different review ID.")
        return job

    def trace_protocol(self):
        """Read the event contract before adapting a producer's telemetry."""
        return self.request("society/protocol")

    def trace_runs(self, limit=50):
        return self.request("society/runs", {"limit": bounded_int(limit, "limit", 1, 100)})

    @staticmethod
    def _trace_path(run_id):
        if not isinstance(run_id, str) or not re.fullmatch(r"society-[a-f0-9]{24}", run_id):
            raise ClientError("invalid_params", "run_id must be a saved society run ID from trace-runs or trace-import.")
        return "society/runs/" + run_id

    @staticmethod
    def _trace_version(version, required=False):
        if version is None and not required:
            return {}
        return {"version": bounded_int(version, "version", 1, 1_000_000_000)}

    def trace_import(self, payload):
        """Persist declared events in the separate workspace, not the historical corpus."""
        if not isinstance(payload, dict) or payload.get("schema_version") != "societylab.events.v1":
            raise ClientError("invalid_params", "payload must be a societylab.events.v1 JSON object with schema_version.")
        if not isinstance(payload.get("source"), dict) or not isinstance(payload.get("run"), dict):
            raise ClientError("invalid_params", "payload requires source and run objects.")
        if not isinstance(payload.get("events"), list) or not 1 <= len(payload["events"]) <= 2000:
            raise ClientError("invalid_params", "events must contain 1–2000 entries; the server also enforces accumulated run bounds.")

        def check_depth(value, depth=0):
            if depth > 12:
                raise ClientError("invalid_params", "Trace JSON exceeds 12 levels of nesting.")
            if isinstance(value, dict):
                for item in value.values():
                    check_depth(item, depth + 1)
            elif isinstance(value, list):
                for item in value:
                    check_depth(item, depth + 1)
        check_depth(payload)
        try:
            # Match request() serialization, so bytes checked equal bytes transmitted.
            encoded = json.dumps(payload, allow_nan=False).encode()
        except (ValueError, TypeError, UnicodeError):
            raise ClientError("invalid_params", "Trace payload must contain finite, valid JSON values.") from None
        if len(encoded) > MAX_TRACE_BYTES:
            raise ClientError("invalid_params", "Serialized trace payload exceeds 1 MiB.")
        try:
            return self.request("society/runs", body=payload)
        except ClientError as exc:
            if exc.status == 409:
                raise ClientError("conflict", "Trace import conflicts with saved source/run metadata or event IDs; inspect the saved run before changing or retrying the payload.", 409) from None
            if exc.code == "connection":
                raise ClientError("connection", "Trace import was not confirmed; it may have been saved. Inspect trace-runs before retrying. Preserve stable event IDs and the exact payload.") from None
            raise

    def trace_run(self, run_id, version=None):
        return self.request(self._trace_path(run_id), self._trace_version(version))

    def trace_graph(self, run_id, version, seed, hops=1):
        path = self._trace_path(run_id) + "/graph"
        params = self._trace_version(version, required=True)
        if not isinstance(seed, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", seed):
            raise ClientError("invalid_params", "seed must be an event ID of 1–128 supported characters.")
        params.update(seed=seed, hops=bounded_int(hops, "hops", 0, 2))
        return self.request(path, params)

    def trace_review(self, run_id, version, question=None):
        path = self._trace_path(run_id)
        params = self._trace_version(version, required=True)
        if question is None:
            return self.request(path + "/review", params)
        body = {**params, "question": text(question, "question", 4000, True)}
        return self.request(path + "/investigate", body=body)

    def export(self, q="", source=None, agent_id=None, table=None, from_time=None, to_time=None, limit=30, cursor=0):
        args = dict(q=q, source=source, agent_id=agent_id, table=table, from_time=from_time, to_time=to_time, limit=limit, cursor=cursor)
        return {"format": "observatory-evidence-page-v1", "query": args, "limitations": LIMITATIONS, "evidence": self.search(**args)}

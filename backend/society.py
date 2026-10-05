"""Authenticated by app.py: bounded Society Lab intake, replay and review.

The historical corpus stays read-only. This adapter persists producer-declared
events in a separate database and makes no provider calls or executable imports.
"""
from collections import Counter, defaultdict
from contextlib import contextmanager
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3

from fastapi import APIRouter, HTTPException, Query, Request
try:
    from .vendor.society_lab import observability_protocol as protocol
    from .vendor.society_lab.event_evidence_graph import build_event_evidence_neighborhood
    from .vendor.society_lab.store import clean, fingerprint, now
except ImportError:
    from vendor.society_lab import observability_protocol as protocol
    from vendor.society_lab.event_evidence_graph import build_event_evidence_neighborhood
    from vendor.society_lab.store import clean, fingerprint, now

router = APIRouter(prefix="/society", tags=["Society Lab"])
_intake_slots = asyncio.Semaphore(2)
INTAKE_WAIT_SECONDS = 1
MAX_OBSERVATIONS = 50
LIMITATIONS = list(protocol.LIMITATIONS) + [
    "Checks compare declared fields in capture order; they do not verify the external world or establish causal effects.",
    "A failure followed by a completion report is a review lead, not proof that completion is false.",
    "Imported runs remain separate from the indexed historical corpus. No classifier, experiment or paid model is launched.",
]


def reference(record):
    return {key: record[key] for key in ("id", "version", "hash")}


def _identity(identity):
    if type(identity) is not str or not re.fullmatch(r"society-[a-f0-9]{24}", identity):
        raise ValueError("Use a saved society run ID")


def evidence_checks(record):
    """Zero-call, field-based leads with exact source IDs, never trait scores."""
    events = record["payload"]["events"]
    calls, receipts, artifacts = defaultdict(list), defaultdict(list), defaultdict(list)
    observations = []

    def add(kind, title, ids, detail):
        observations.append({"id": "check-" + protocol.digest([kind, ids])[:16],
            "kind": kind, "title": title, "event_ids": ids,
            "detail": detail, "status": "review_lead", "basis": "declared_fields_in_capture_order"})

    for position, event in enumerate(events):
        if event["kind"] == "tool.called":
            calls[event["data"]["call_id"]].append(event)
        elif event["kind"] == "tool.returned":
            receipts[event["data"]["call_id"]].append(event)
        elif event["kind"] == "artifact.updated":
            artifacts[event["data"]["artifact_id"]].append(event)

    for call_id, group in calls.items():
        for call in group:
            matches = [r for r in receipts[call_id] if r.get("actor_id") == call.get("actor_id")]
            if not matches:
                add("call_without_receipt", "Tool call has no matching receipt", [call["id"]],
                    "No same-actor return for this call ID is captured in this run version. The result may be outside the capture.")
    for call_id, group in receipts.items():
        for receipt in group:
            matches = [c for c in calls[call_id] if c.get("actor_id") == receipt.get("actor_id")]
            if not matches:
                add("receipt_without_call", "Tool receipt has no matching call", [receipt["id"]],
                    "No same-actor call with this ID is captured. This is missing linkage, not proof of fabricated execution.")

    latest = {}
    completions = defaultdict(list)
    for event in events:
        task = event.get("task_id")
        if not task:
            continue
        if event["kind"] == "tool.returned":
            latest[task] = event
            for completed in completions[task][-1:]:
                add("completion_precedes_receipt", "Completion was captured before a later tool receipt",
                    [completed["id"], event["id"]],
                    "Capture order places this task completion before a later receipt for the same declared task. Producer timestamps are not a shared causal clock.")
        elif event["kind"] == "task.completed" and event["data"]["success"]:
            prior = latest.get(task)
            if prior and not prior["data"]["success"]:
                add("completion_after_failed_receipt", "Completion follows a failed tool receipt",
                    [prior["id"], event["id"]],
                    "The latest preceding captured receipt for this task reports failure, followed by a successful completion report. Other recovery or independent completion may be unrecorded.")
            completions[task].append(event)

    for artifact_id, group in artifacts.items():
        revisions = {event["data"]["revision_id"] for event in group}
        if len(revisions) > 1:
            add("artifact_revision_chain", "Shared artifact has multiple recorded revisions",
                [event["id"] for event in group[:20]],
                f"{len(group)} update events declare {len(revisions)} distinct revisions. Capture order does not prove overwriting, loss, or which version a recipient saw.")
        by_revision = defaultdict(list)
        for event in group:
            by_revision[event["data"]["revision_id"]].append(event)
        for revision in by_revision.values():
            hashes = {event["data"].get("content_sha256") for event in revision} - {None}
            if len(hashes) > 1:
                add("revision_hash_conflict", "One revision ID declares different content hashes",
                    [event["id"] for event in revision[:20]],
                    "This source declares different SHA-256 values for the same artifact revision. Inspect the producer and source records before interpreting behavior.")
    counts = dict(Counter(row["kind"] for row in observations))
    return {"source_ref": reference(record), "evidence_status": "producer_declared",
        "observations": observations[:MAX_OBSERVATIONS], "counts": counts,
        "observation_count": len(observations), "truncated": len(observations) > MAX_OBSERVATIONS,
        "limits": {"observations": MAX_OBSERVATIONS, "events": protocol.MAX_EVENTS},
        "provider_calls": 0, "limitations": LIMITATIONS}


class SocietyStore:
    def __init__(self, path=None):
        corpus = Path(os.environ.get("OBSERVATORY_DB", "data/evidence.sqlite")).expanduser()
        self.path = Path(path or os.environ.get("SOCIETY_DB") or corpus.with_name("society.sqlite")).expanduser()
        if self.path.resolve() == corpus.resolve():
            raise ValueError("SOCIETY_DB must be separate from the historical corpus")

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS society_runs(id TEXT,version INTEGER,created TEXT,payload TEXT,hash TEXT,PRIMARY KEY(id,version));
                CREATE TABLE IF NOT EXISTS society_batches(id TEXT,batch_hash TEXT,version INTEGER,PRIMARY KEY(id,batch_hash));
            """)
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def decode(row):
        if row is None:
            raise KeyError("Run version is not available")
        record = dict(row)
        record["payload"] = json.loads(record["payload"])
        record["kind"] = "observability_run"
        if fingerprint(record["payload"]) != record["hash"]:
            raise ValueError("Saved run integrity check failed")
        return record

    def get(self, identity, version=None):
        _identity(identity)
        if version is not None and (type(version) is not int or not 1 <= version <= 1000000000):
            raise ValueError("Run version must be a positive integer")
        with self.connect() as db:
            query = "SELECT * FROM society_runs WHERE id=?"
            params = [identity]
            if version is not None:
                query += " AND version=?"
                params.append(version)
            return self.decode(db.execute(query + " ORDER BY version DESC LIMIT 1", params).fetchone())

    def list(self, limit=50):
        with self.connect() as db:
            rows = db.execute("SELECT r.* FROM society_runs r JOIN (SELECT id, MAX(version) AS version FROM society_runs GROUP BY id) latest USING(id,version) ORDER BY r.created DESC LIMIT ?", (limit + 1,)).fetchall()
            records = [self.decode(row) for row in rows[:limit]]
        return {"runs": [{**reference(record), "created": record["created"],
            "source": record["payload"]["source"], "run": record["payload"]["run"],
            "event_count": len(record["payload"]["events"])} for record in records],
            "truncated": len(rows) > limit, "limits": {"runs": limit}}

    def append(self, raw):
        original = protocol.parse_batch(raw)
        batch = clean(original)
        protocol.validate_batch(batch)
        identity = "society-" + protocol.digest({"source": batch["source"]["id"], "run": batch["run"]["id"]})[:24]
        batch_hash = protocol.digest(original)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            latest_row = db.execute("SELECT * FROM society_runs WHERE id=? ORDER BY version DESC LIMIT 1", (identity,)).fetchone()
            latest = self.decode(latest_row) if latest_row else None
            prior_batch = db.execute("SELECT version FROM society_batches WHERE id=? AND batch_hash=?", (identity, batch_hash)).fetchone()
            if prior_batch:
                record = self.decode(db.execute("SELECT * FROM society_runs WHERE id=? AND version=?", (identity, prior_batch["version"])).fetchone())
                return {"run": record, "latest_ref": reference(latest), "idempotent": True, "added_events": 0, "checks": evidence_checks(record)}
            if latest:
                for key in ("source", "run"):
                    if protocol.canonical(latest["payload"][key]) != protocol.canonical(batch[key]):
                        raise ValueError("Source and run metadata are immutable; use a new run ID")
            existing = latest["payload"]["events"] if latest else []
            by_id = {event["id"]: event for event in existing}
            added = []
            for event in batch["events"]:
                if event["id"] in by_id:
                    if protocol.canonical(event) != protocol.canonical(by_id[event["id"]]):
                        raise ValueError("Conflicting event ID; captured events cannot be rewritten")
                else:
                    added.append(event)
            combined = {**batch, "events": existing + added}
            protocol.validate_batch(combined)
            if latest and not added:
                record = latest
            else:
                payload = protocol._run_payload(combined, reference(latest) if latest else None,
                    hashlib.sha256(raw).hexdigest(), batch_hash, original != batch)
                payload["limitations"] = LIMITATIONS
                # Reference count is also bounded before accepting a run whose graph would be unrenderable.
                if sum(payload["reference_checks"]["counts"].values()) > 20000:
                    raise ValueError("Run exceeds the 20,000 reference-check limit")
                record = {"id": identity, "kind": "observability_run", "version": latest["version"] + 1 if latest else 1,
                    "created": now(), "hash": fingerprint(payload), "payload": payload}
                db.execute("INSERT INTO society_runs VALUES(?,?,?,?,?)", (identity, record["version"], record["created"], json.dumps(payload, ensure_ascii=False, allow_nan=False), record["hash"]))
            db.execute("INSERT INTO society_batches VALUES(?,?,?)", (identity, batch_hash, record["version"]))
        return {"run": record, "latest_ref": reference(record), "idempotent": not added,
            "added_events": len(added), "checks": evidence_checks(record)}


def _store():
    return SocietyStore()


async def _append_bounded(raw):
    """Keep SQLite work off the event loop and count cancelled in-flight writes.

    A disconnected caller does not stop its thread. Retain its slot until the
    actual write finishes; stable batch IDs make subsequent retries idempotent.
    """
    slots = _intake_slots
    try:
        await asyncio.wait_for(slots.acquire(), INTAKE_WAIT_SECONDS)
    except TimeoutError:
        raise HTTPException(503, "Trace intake is busy; retry the same batch shortly.", headers={"Retry-After": "1"}) from None
    try:
        worker = asyncio.create_task(asyncio.to_thread(lambda: _store().append(raw)))
    except BaseException:
        slots.release()
        raise

    def finished(task):
        slots.release()
        # Retrieve a detached failure too, without echoing data or changing the
        # exception observed by a caller still awaiting this task.
        if not task.cancelled():
            task.exception()

    worker.add_done_callback(finished)
    return await asyncio.shield(worker)


def _run(identity, version):
    try:
        return _store().get(identity, version)
    except KeyError:
        raise HTTPException(404, "Run version is not available") from None


def manifest():
    # Reconstruct the transport manifest; never advertise upstream local-server credentials/endpoints.
    example = json.loads((Path(__file__).resolve().parents[1] / "examples" / "society-events.json").read_text())
    return {"schema_version": protocol.VERSION, "title": "Society Lab event intake",
        "maximum_bytes": protocol.MAX_BYTES, "maximum_events_per_accumulated_run": protocol.MAX_EVENTS,
        "maximum_json_depth": protocol.MAX_DEPTH, "source_kinds": ["telemetry", "authored_example"],
        "kinds": {kind: {"data_required": sorted(required), "data_optional": sorted(optional)} for kind, (required, optional) in protocol.DATA_FIELDS.items()},
        "post_endpoint": "/v1/society/runs", "authentication": "Existing Observatory Bearer authentication",
        "append_contract": "Fixed source/run metadata; stable event IDs; exact retries return their historical version; conflicting IDs and accumulated overflow reject atomically.",
        "example": example, "model_calls": 0, "limitations": LIMITATIONS,
        "upstream": {"repository": "https://github.com/Atharvap14/society-lab", "commit": "ac71dc81941c68da21fd7d7ccfcad61ca09737db"}}


@router.get("/protocol")
def get_protocol():
    return manifest()


@router.get("/runs")
def list_runs(limit: int = Query(50, ge=1, le=100)):
    return _store().list(limit)


@router.post("/runs")
async def append_run(request: Request):
    length = request.headers.get("content-length")
    if length is not None:
        try:
            if int(length) < 0 or int(length) > protocol.MAX_BYTES:
                raise HTTPException(413, "Event batch exceeds 1 MiB")
        except ValueError:
            raise HTTPException(400, "Invalid Content-Length") from None
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > protocol.MAX_BYTES:
            raise HTTPException(413, "Event batch exceeds 1 MiB")
        raw.extend(chunk)
    return await _append_bounded(bytes(raw))


@router.get("/runs/{identity}")
def get_run(identity: str, version: int = Query(None, ge=1, le=1000000000)):
    record = _run(identity, version)
    review = evidence_checks(record)
    return {"run": record, "checks": review, "review": review}


@router.get("/runs/{identity}/graph")
def graph(identity: str, seed: str, version: int = Query(..., ge=1, le=1000000000), hops: int = Query(1, ge=0, le=2)):
    return build_event_evidence_neighborhood(_run(identity, version), seed_event_id=seed, hops=hops)


@router.get("/runs/{identity}/review")
def review(identity: str, version: int = Query(..., ge=1, le=1000000000)):
    return evidence_checks(_run(identity, version))

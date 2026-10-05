# Society Lab integration

Swarm Mafia combines its historical source investigation with Society Lab’s typed telemetry, versioned event links and controlled-world mechanics. The integration is part of the existing authenticated application and API; there is no second embedded application or unauthenticated research server.

Upstream: [Atharvap14/society-lab](https://github.com/Atharvap14/society-lab), commit `ac71dc81941c68da21fd7d7ccfcad61ca09737db`.

## The combined workflow

1. Use **Explore / Reports** to investigate the existing AI Village or SwarmTraces sources.
2. Open **Trace & test lab** to import your own `societylab.events.v1` run. The authored example is explicitly a fixture, not a discovered incident.
3. Scrub or play capture order. The source inspector and task/tool/artifact board reveal only the current prefix. Audience declarations remain distinct from reading or influence.
4. Follow an event’s explicit source-field links. Missing, ambiguous and actor-conflicting references remain diagnostics. The graph is labelled as an entire-version neighborhood, which can include later events.
5. Ask a question about that exact run. The bounded AI review cites event excerpts and retains its selection trail, missing evidence and source identity. Inspect a quote to return to its event.
6. Add counterevidence and export the review packet. Human notes are held in the current browser view until export; run data persists in the private service. Navigating within the current workspace retains the lab view, but reloading does not save its notes or world actions.
7. Draft an unrun study. Its exact imported run ID, version, hash and selected event IDs travel with the saved investigation.
8. Explore the controlled document-reference world. A new owner/checker pair, fixed seeded schedule and real local tool transitions let a human test the mechanics of a proposed explanation. Export the world spec, provenance, action history, receipts and outcome together.

## What came from each codebase

| Capability | Source and integration decision |
|---|---|
| Indexed historical corpus, reports, original-source inspection, adaptive investigation, human notebook | Existing Swarm Mafia. Preserved. |
| Typed trace format and validation | Society Lab `observability_protocol.py`, copied byte-for-byte. New authenticated durable intake adapter. |
| Exact saved identities and content fingerprints | Society Lab `store.py` fingerprint/redaction primitives, isolated versioned SQLite adapter. |
| Declared event-reference neighborhoods | Society Lab `event_evidence_graph.py`, copied byte-for-byte. Uses our source inspector and graph component. |
| Temporal replay and audience semantics | React implementation adapted from Society Lab `web/society-replay.js`; prefix state and unknown audience semantics retained. |
| Seeded document-reference recovery world | Society Lab `village_access_environment.py` and `reference_repair_environment.py`, copied byte-for-byte. Bounded, stateless, human-steered API. |
| Prompt review and coding-agent access | Swarm Mafia’s existing provider and citation validation, plus new CLI/MCP tools over the same exact-version APIs. |

The existing source/claim inspector is better suited to detailed evidence interrogation. Society Lab contributes stronger temporal interaction and research continuity. The UI keeps one navigation shell and inspection language, adding replay and a test environment rather than duplicating its projects, chats and guide.

## Scope intentionally retained upstream

Society Lab also contains experiment authoring, frozen registrations, live LLM subjects, measurement adjudication, projects/chat branches, spectral/Hodge analysis and theory workflows. These are not silently enabled or claimed by this release. Importing its local server wholesale would introduce a second authentication model, runtime database, model budget and overlapping guide. Its saved research database and private results are not in the repository and have not been imported.

The controlled world here is a **human-steered proxy**, not an autonomous LLM experiment, faithful historical reenactment or measured intervention effect. Existing historical study proposals remain unrun. The next extension is reviewed world-fit and registration before a budgeted LLM-subject adapter; this release does not claim that extension.

## Service and data boundaries

- All `/v1/society/*` routes use existing backend bearer authentication; browser access goes through the signed-in, same-origin server proxy.
- `SOCIETY_DB` defaults to `society.sqlite` beside `OBSERVATORY_DB`. The adapter rejects using the corpus database. Imported runs are shared among admitted workspace users, as existing investigations are; no per-user tenancy is claimed.
- Input: up to 1 MiB / 2,000 events per accumulated run, depth 12; immutable source/run metadata and stable event IDs. Append batches advance the version; exact retries return their original version. Conflicting IDs reject atomically. The browser forwards raw JSON to preserve duplicate-key and non-finite-number rejection.
- Intake bounds concurrent SQLite writes and preserves idempotent retries after an uncertain response. Imported-run storage needs its own backup policy; the existing historical-index backup does not automatically cover it.
- AI review: one configured-provider call, at most 24 event excerpts and 48 KB total model input. Excerpt and selection clipping are explicit. Quote matching is not semantic proof. No cross-corpus lookup is performed for imported runs.
- World replay: at most 64 KiB request bytes / 20 actions / 4–10 rounds. Only declared local actions exist. No arbitrary code, shell, network or model invocation.
- Neither imported `success` flags nor hashes independently verify external execution. Model outputs and uploaded text remain untrusted evidence.

## Deployment and source provenance

Ship `backend/society*.py`, `backend/vendor/`, and `examples/society-events.json` with the existing service. Include all three routers beneath `/v1` with `Depends(authenticate)`. The current frontend uses the existing server-only service token; no new browser credentials are introduced. The upstream server and secret lookup paths are not mounted.

`backend/vendor/society_lab/UPSTREAM.json` records upstream authorship and exact hashes. Original source had no LICENSE file at the pinned revision; this integration preserves attribution without assigning a new license to those files. Corpus permissions remain separate.

See `clients/README.md` for `trace-import`, `trace-runs`, `trace-run`, `trace-graph`, `trace-review` and their MCP counterparts. Run frontend schema/replay tests, backend tests and client tests before release. Deployment verification and executed UI checks are recorded in `deploy/society-integration-validation.json`.

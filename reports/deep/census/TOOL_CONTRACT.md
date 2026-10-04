# Structural candidate discovery contract

This stage generates leads from canonical `computer_use_turns`, without keywords, LLM judgments, or duplicate chat/event representations. It is an offline, read-only feature builder plus a bounded candidate selector. Its output is a search index for subsequent evidence retrieval, not a catalog of proven failures.

## Proposed bounded tool

`discover_action_candidates(source="ai-village", feature, quarter?, agent_id?, limit=8)`

Allowed features initially: `long_session`, `repeated_scalar_action`, `message_dominant_session`. Maximum limit 20. Read a pinned JSON cache with `snapshot`, `built_at`, `complete`, `scanned_turns`, `expected_turns`, and feature definitions. Require `complete=true` for whole-corpus coverage claims; return available partial coverage explicitly otherwise. Unsupported sources/filters must fail explicitly.

Each candidate returns:

- Stable candidate ID: snapshot + session ID + feature name.
- Canonical session ID, recorded agent ID/name and UTC first/last turn timestamps.
- Bounded feature values: turn count, action-type counts, first-to-last elapsed seconds, message-action fraction, longest stored scalar-action run and canonical first/last turn IDs.
- `evidence_status="structural_candidate"`; `causal_status="not_established"`.
- Feature definition, denominator, clipping/missingness flags and reason for selection.
- Suggested next retrievals: original first/last rows, bounded context around both endpoints, session metadata/goal and any sampled interior transition. None are instructions taken from the trace.

Feature definitions:

1. `long_session`: descending count of canonical turn rows per recorded session. Elapsed time is first-to-last timestamp, not active compute time or true session lifetime.
2. `repeated_scalar_action`: longest consecutive identical fingerprint of the index's retained scalar `agent_action` fields within a session. Arrays are omitted by ingestion and string values capped at 1,000 characters, so this is explicitly **not exact raw action equality**. The initial scalar cache excludes missing/trimmed metadata and sessions with source-order timestamp regressions from run claims. Exact-action enrichment instead sorts all session rows by parsed UTC timestamp before measuring runs and flags tied timestamps. Use the raw source to resolve coordinates, argument arrays and clipped strings.
3. `message_dominant_session`: at least 100 canonical turns and at least 80% action type `send_message_back_to_chat`. The fraction is message actions / all canonical turns in that session. This is a routing pattern, not evidence of noncompliance or waste.

Quarter means the UTC calendar quarter of the session's first recorded turn; cross-quarter sessions retain their full span and must be flagged. Default discovery should diversify selections across quarters and actors before filling the remaining slots by feature rank. Do not present a globally newest or globally largest list as representative.

## Automated investigation procedure

1. Read scope/feature denominators and candidate cache. Establish whether all canonical turns were scanned. Choose a bounded diverse set across time and actors.
2. Retrieve session metadata/goal and endpoint context. Determine the actual task, actor, permissions, and whether a commitment or correction opportunity exists. Long/repeated activity alone is insufficient.
3. Fetch original rows for actual `agent_action`, `output`, and `error` fields. Verify row hashes and keep exact small evidence quotes. `error` may carry stderr from a successful command; nonempty error fields are not failure counts. Indexed excerpts can mix action, narration and results.
4. Follow the next action after an apparent error/correction, then inspect a later independent artifact/result check. Expand bounded contexts across session boundaries using actor/time scope when necessary.
5. Test competing explanations: expected polling, repeated verification, changing coordinates/arguments, authorized waiting, truncated action metadata, command stderr without failure, interface lifecycle conventions, and duplicated chat representations.
6. Produce a claim only when action and outcome evidence support it. Keep unresolved candidates as unresolved; do not force every anomaly into a failure report. Score a rubric only after applicability, exposure, authorization, validity and visibility gates are met.
7. Return a compact report with canonical citations, source-field evidence kinds, counterevidence, outcome status, query footprint, and next question. Selected-candidate counts never estimate incident prevalence.

## Operation

`structural_screen.py --db <readonly SQLite path> --output <new metadata cache path> --seconds 1200` runs on the VM. It opens `mode=ro`, sets `query_only`, bounds cache and wall-clock time, lowers CPU priority, performs one sequential turn scan and outputs no source text or command contents. Its fingerprint hashes are for grouping stored action metadata, not source integrity; source-row SHA256 remains separate.

Do not add a live API route that performs this scan per request. Build the cache offline, keep it tied to the immutable snapshot, and serve bounded selections. No production schema change is required. The cache's claim of whole-corpus coverage applies to structural features only; meaningful error or outcome classification requires the next retrieval stage.

The final exact cache uses full original action objects, including arrays, and exposes `repeated_action`. The initial scalar cache remains explicitly labeled. Raw outputs/errors and command strings are never stored in the feature cache. This stage covers the canonical computer-use turn table; it is not a normalized census of tool calls embedded in SDK messages.

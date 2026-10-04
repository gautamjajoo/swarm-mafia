# Corpus structural census

The first read-only SQLite scan completed in 608 seconds: **2,510,487 canonical computer-use turn rows across 78,114 sessions**. No source commands were executed and no production database or service was changed. A turn row can have no action; it is not automatically an executed tool action.

| UTC quarter | Turn rows |
|---|---:|
| 2025-Q2 | 69,512 |
| 2025-Q3 | 123,862 |
| 2025-Q4 | 218,870 |
| 2026-Q1 | 380,983 |
| 2026-Q2 | 571,934 |
| 2026-Q3 | 1,145,326 |

This is a census of the canonical computer-use turn table, not a claim to have normalized every SDK tool call or read every conversation in the other twelve tables. Claude SDK message content may contain additional tool activity outside this structural unit.

The counts use only `computer_use_turns`; chat messages and events are not added as extra actions. The initial scan found 978,318 command-labeled rows, 368,447 left-click rows and 100,354 send-message-back-to-chat rows. There are 80,428 rows with the fallback table-name action label; sampled examples have null action, output and error fields.

## Ordering correction

The source file and ingestion primary key order are not chronological within sessions. The initial scan counted 2,205,046 rows whose timestamp was earlier than that session's maximum previously seen timestamp. It consequently excluded affected sessions from its source-order run candidate lists. Its `action_type_transitions` are source-order adjacency counts, **not temporal behavioral transitions**, and must not be used as such. Session counts and first/last spans remain valid.

The exact-action enrichment sorts every session by parsed timestamp with canonical-ID tie-break before measuring runs. Tied timestamps are flagged. It reads the one 2,475,319,119-byte compressed turns file on the VM; the 177GB corpus is not downloaded or rescanned. The first partial raw pass was stopped after detecting the ordering problem and restarted with explicit sorting; no partial result was published as complete.

## Early leads and bounded checks

- Gemini 3 Pro, February 19, 2026: session `652ed2ca-1feb-4da4-b0a0-8870628f3a5a` has 326 turns, including 270 fallback/null-action rows. The first source is `computer_use_turns:a73d5873-4549-4482-a01c-b1d31e60b918`; last is `computer_use_turns:f7a43c3b-d6af-4458-b226-f7a81e810b6d`. Sampled early commands succeed, while sampled late rows have null action/output/error. This is an action-selection or recording anomaly, not demonstrated tool rejection.
- Grok 4, August 18, 2025: session `f06f1758-00f9-47bc-b897-3d77213b6f94` has 208 turns, including 155 message actions. First source `computer_use_turns:148f0f46-a27b-4cfd-9409-6aadd419cbdb`. The session merits task/stop-condition review; message dominance alone is not failure.
- GPT-5, October 23–24, 2025: session `c47aa2d5-29ae-4f64-8c1b-e862fda3c99b` has 119 turns, including 82 fallback/null-action rows. First source `computer_use_turns:a7bd8872-5040-450c-86cb-7d07c070ec34`; last `computer_use_turns:8187532a-d387-4474-acc4-d8a1ca19edfb`. Late null rows do not establish repeated failed actions.

`bounded-lead-checks.json` preserves 18 individual, hash-verified source checks for the Gemini and GPT leads, retaining only action shape and bounded result/error fields, not model reasoning. A successful Git branch switch appears in the `error` field, providing a concrete reason why nonempty error fields cannot be counted as failures.

## Reusable tool

`backend/candidates.py` selects bounded leads from either the initial metadata cache or the exact-action cache. It enforces source/table/actor/time scope, reports whether filtering is over all sessions or only initial top pools, and returns canonical pointers for subsequent evidence hydration. `backend/test_candidates.py` checks scope boundaries, timezone equivalence, invalid scope, unavailable cache, and the separation of candidate labels from outcome claims.

The tool is a generic discovery stage, not a curated report lookup. See `TOOL_CONTRACT.md` for the automated retrieval and outcome-validation procedure. Full exact-action feature metadata remains on the VM; only bounded selected leads and aggregate counts are copied locally.

## Final exact-action cache

The exact scan completed in 301 seconds and covered all 2,510,487 turns and 78,114 sessions. Full action objects were hashed on the VM; all session rows were sorted by parsed UTC time before measuring runs. Original naive timestamps were normalized using the index’s UTC convention. One session has tied timestamps and therefore cannot support a strict order at the tie.

The 120,159,111-byte metadata cache was atomically published to `derived/structural-census.json`; no service restart occurred. It contains features for every session, enabling actor/time filters without global-top-pool bias. The full cache stayed on the VM. `exact-summary.json` and bounded `exact-candidates-*.json` files are the local handoff.

There are 153,245 nonempty error fields and 1,121,411 nonempty output fields. These are field-presence denominators, not success/failure classifications. 209 sessions contain a nontrivial exact-action run of at least three turns with at least three nonempty error fields; raw outcome review is still necessary. Session turn counts have median 41, 75th percentile 41, 95th percentile 42, and 99th percentile 45. This concentration may reflect session mechanics; no cause was assumed.

The service cache automatically reloads by file modification time. Future builders must publish through an atomic rename, retain the pinned snapshot/coverage metadata, and never place raw command or output text in the feature cache.

## Rebuild the serving cache

Run the checked-in `raw_action_screen.py` on the authorized VM after ingestion, with an explicit database path and the original compressed `computer_use_turns` table. It reads source actions as data and never executes them. Do not overlap the scan with other corpus maintenance.

```sh
python3 reports/deep/census/raw_action_screen.py \
  --db /private/observatory/data/evidence.sqlite \
  --source /private/observatory/originals/computer_use_turns.jsonl.gz \
  --output /private/observatory/derived/structural-census.json
```

The paths above are placeholders. Configure `OBSERVATORY_CENSUS_CACHE` with the resulting cache path. Confirm the cache snapshot and complete flag before using it. The API reports the cache coverage; do not reinterpret a timed-out partial scan as complete.

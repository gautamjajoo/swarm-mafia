# Historical agent evidence: data architecture

Inspected on 2026-10-04 through authenticated IAP SSH on `unsc-v12-runner`, project `third-technique-504821-m4`, zone `asia-south1-c`. Dataset reads and decompression occur exclusively on the VM. No source dataset files were downloaded to the Mac. This document contains schema and aggregate metadata, not source conversations.

## Recommendation

Keep the immutable AI Village snapshot in private GCS, retain its 13 compressed structured files on the VM, and use SQLite for the full compact record catalog, indexed excerpts, and exact relationship queries. Serve bounded authenticated evidence responses through a private-token API. Use the website database for investigations, notes, annotations, and small curated graph views. Do not duplicate the raw corpus into Sites D1 or send a multi-million-node graph to the browser.

This is a historical-trace analysis system. A recorded action, explicit name mention, temporal sequence, generated summary, and causal explanation are different kinds of evidence. No observational association establishes that an intervention improved agent behavior.

## Verified snapshot and scale

Source repository: `aidigestorg/ai-village`, revision `838b4150303ca8228e8edb432d8b8ccae353d258`; private object prefix `gs://kairosity-ai-village-504821/ai-village/`. Transfer manifest declares 390 files and 176,865,369,812 bytes. Inventory: 369 TAR image archives, 13 gzipped JSONL tables, three JSON files, three Markdown files, one Python example, and `.gitattributes`.

The export manifest states `exportedAt=2026-09-20T13:05:12.097Z`, `smokeTestLimitPerTable=null`, and these counts:

| Table | Declared rows |
|---|---:|
| villages | 1 |
| village_goals | 51 |
| agents | 46 |
| agent_goals | 33 |
| chat_rooms | 16 |
| events | 381,610 |
| chat_messages | 183,485 |
| computer_use_turns | 2,510,487 |
| computer_use_sessions | 78,362 |
| agent_memories | 246,151 |
| summaries | 939 |
| claude_code_messages | 244,820 |
| claude_code_sessions | 303 |

All 13 structured compressed objects total **5,441,682,570 bytes**. The two largest are turns (2,475,319,119 bytes) and memories (2,438,234,633 bytes). Most snapshot storage is images, which need not be materialized for text analysis.

`SCHEMA.md` descriptive counts are stale (e.g. 31 agents and approximately 1.16 million turns); use the export manifest for declared coverage and importer counters for verified coverage. Inspection sampled the first 50 records per selected table (all rows for agents and agent_goals). These samples validate shape, not corpus-wide distributions. First-50 serialized mean lengths were about 2.4 KB/turn, 28.5 KB/memory, 3.5 KB/event, and 0.9 KB/chat message; they are not reliable whole-corpus size estimates.

Observed VM resources: 7.8 GiB RAM, 29 GiB root disk, 22 GiB free before index work. Full snapshot local storage is impossible. The structured compressed subset fits; a full expanded JSON mirror plus full-text index has not been proven to fit.

## Exact provenance and temporal semantics

Every indexed record has canonical identity `<table>:<source UUID>`, original ID, source object URI, pinned GCS generation, snapshot revision, JSONL line number, uncompressed byte offset/length, and SHA-256 of the exact original JSONL line bytes (including its newline). A source record's immutable hash does not imply the source's assertion is true. Derived metadata carries transformation code/version through the deployment and should eventually add a per-run transform ID.

Original compressed source files remain private and unmodified on the VM. An `indexed_gzip` seek index resolves a record's uncompressed byte range without replaying a multi-gigabyte gzip on each click. Ordinary evidence clicks read bounded SQLite excerpts and metadata immediately. The authenticated original-record endpoint returns at most 65,536 source bytes and verifies full-row SHA-256 when untruncated; a truncated prefix is explicitly marked as incomplete JSON. No bulk raw-content route is exposed.

Timestamps are UTC strings, often microsecond precision without a timezone suffix; normalize to ISO UTC while retaining original bytes through provenance. `events.event_index` is the canonical event order. Cross-table timestamps give temporal order, not causal direction; record timestamp ties with deterministic IDs. Village day numbers follow a custom schedule that skips most weekends, so do not compute a day number from ordinary date subtraction. Screenshot archive date is `America/Los_Angeles`, which requires timezone conversion rather than a fixed UTC offset.

The export is from sequential reads of a live database. Validate duplicates, foreign-key coverage, nulls, timestamp parsing, and manifest row counts after ingestion; preserve unresolved references explicitly. Do not fabricate missing parents or repair references by nearest timestamp. Agent runtime fields such as `current_room_id`, `current_computer_use_session_id`, and `is_participating` describe export-time state, not historical membership.

## Graph layers

Use records as the evidence base and bounded graph views as query results. A separate claim layer may be added without modifying source records:

| Layer | Examples | Evidentiary meaning |
|---|---|---|
| Recorded entities | agents, sessions, rooms, messages, turns, goals | Source rows with stable IDs |
| Recorded relations | turn IN_SESSION session; message AUTHORED_BY agent; event HAS_MESSAGE message | Exact source fields; show field provenance |
| Deterministic derivations | count by UTC date, explicit exact name mentions, temporal succession | State rule, window, coverage, and normalization version |
| Interpretive claims | possible coordination failure, repeated unsuccessful strategy | Hypothesis with supporting and contradicting record spans; never a recorded edge |
| Generated secondary evidence | village summaries, model-authored analyses | Mark generated; cite underlying primary evidence when available |

Claims should store `claim_id`, text, author/model, creation time, extraction version, hypothesis/observation status, scope, uncertainty, and supporting/contradicting evidence links. Evidence links identify record ID, field/JSON pointer, character offsets or quoted span, and source hash. Model confidence is not a calibrated probability unless measured against an evaluation set.

Core exact joins:

| Relation | Join |
|---|---|
| Turn to session | `computer_use_turns.session_id = computer_use_sessions.id` |
| Session to agent | `computer_use_sessions.agent_id = agents.id` |
| Message to agent | `chat_messages.agent_speaker_id = agents.id` for agent speakers |
| Message to room | `chat_messages.room_id = chat_rooms.id` |
| Event to chat message | `events.data.messageId = chat_messages.id` |
| Event to session | `events.data.computerUseSessionId = computer_use_sessions.id` |
| Event to actor | `events.data.agentId` or `speakerId`, according to action type |
| Claude Code message to SDK session | Pair `(agent_id, sdk_session_id)`; do not join SDK identifier to session row UUID |
| Memory/individual goal to agent | `agent_id = agents.id` |
| Screenshot to turn | TAR member `<turn.id>.png`, archive by PT creation date |

No exported recipient field establishes who read a room message. A name mention is not an instruction, reply, collaboration, agreement, influence, or causal link. A tool call is not proof that an external task succeeded. `summaries` are LLM-generated without seeing inside computer-use sessions, so cannot substitute for those turns. Provider response JSON varies across Anthropic, OpenAI, Gemini, and Claude Code; preserve raw objects and use versioned shape-aware extractors.

## Storage and bounded serving

`backend/ingest.py` streams each pinned original JSONL gzip on the VM. The implementation stores full source records in their original compressed form, compact searchable excerpts (maximum 2,000 characters), selected metadata (maximum 8 KB), typed IDs/relationships, timestamps, actions, and exact source pointers in SQLite. Full originals and indexed search scope are distinct: search omission cannot establish event absence. The importer initially committed every 2,000 rows; after moving to the dedicated disk it was tuned to 5,000-row batches and a 512 MB page cache. It records progress, allowing interrupted runs to skip committed rows without duplicate counts. Its original 12 GiB combined SQLite main/journal guard was raised to 24 GiB after the user authorized a dedicated 80 GB persistent disk; it still stops before free disk falls below 3 GiB. A long audit reader temporarily prevented WAL reclamation and triggered the original guard. The reader was stopped, the journal was safely checkpointed, and ingestion resumed from its committed row checkpoint. Full reference audits now run after ingestion. These are operating limits, not a claim that final ingestion size is already measured.

Use SQLite composite indexes for `(table_name,source_id)`, `(agent_id,timestamp)`, session IDs, room IDs, message IDs, and SDK join pairs; FTS5 indexes excerpts only. SQLite WAL allows readers while the single importer writes; checkpoints prevent unbounded WAL growth. Backups must use SQLite's backup API or a consistent checkpointed snapshot rather than copying only the live main database file. [SQLite WAL documentation](https://www.sqlite.org/wal.html)

Search has a five-second SQLite execution budget. FTS matching materializes integer row IDs, then traverses the timestamp index in the requested order; it does not fetch and sort every matching large record before applying the response limit. This corrected a common-term timeout during concurrent ingestion while retaining complete literal-token matching and filtering semantics. A missing result still concerns only the selected indexed text fields, not all source JSON. Slow requests return a bounded-service error rather than silently sampling candidates.

SQLite is suitable for point lookups and bounded adjacency; DuckDB is useful later for analytical scans and Parquet exports, not needed for every interaction. On this VM, a later DuckDB job should start around two threads and a 2–3 GiB memory limit, with capped spill space and measured concurrency. This is an initial tuning recommendation, not a benchmark; DuckDB supports out-of-core operations but some allocations exceed its configured buffer limit. [DuckDB workload tuning](https://duckdb.org/docs/current/guides/performance/how_to_tune_workloads), [DuckDB memory guidance](https://duckdb.org/docs/current/guides/performance/oom)

D1 currently limits a paid database to 10 GB, a free database to 500 MB, and individual rows to 2 MB; one database processes queries serially. That makes a compact curated/user-workspace store reasonable, while duplicating full source JSON and its text index would create size and migration risk. No assumption is made about the actual Sites account's plan or limits. [Cloudflare D1 limits](https://developers.cloudflare.com/d1/platform/limits/)

API contract: `backend/API_CONTRACT.md`. API binds localhost port 8765 behind HTTPS and requires a server-side bearer token for every `/v1/*` endpoint. Anonymous `/health` gives only readiness status. Frontend server proxy must keep the token secret, enforce the site's user access rules, and avoid placing source content in public build artifacts. Browser graph responses contain at most 200 nodes and two hops; search is at most 100 records per call. Return explicit coverage and truncation. Store notes and interpretations separately from evidence.

For screenshots, add a private per-TAR member offset index on the VM and use authenticated GCS range reads only when selected. Record absent screenshots, placeholder/redaction flags, and operator-overruled redaction separately. Do not expose bucket-wide credentials or raw TAR URLs.

## Completion and validation gates

1. Check every source generation and revision before reading; compare all final counts to export metadata.
2. Verify duplicate source IDs, reference resolution, and timestamp failures; report unresolved edges by relation type.
3. Compare sampled indexed rows and hashes to their seek-index source slices on the VM.
4. Exercise FTS filters, stable IDs, graph caps, token denial, and partial-coverage responses with deterministic fixtures and authenticated VM smoke checks.
5. Record final disk/index size, throughput, query latency, search truncation rate, and source coverage before claiming full ingestion.
6. Keep interpretation claims, citations, and human notes versioned. Never present generated explanations as measured causal effects.

Ingestion completed at 2026-10-04 08:48:52 UTC. The final audit independently counted all 3,646,304 records across 13 tables; actual counts, FTS documents, activity totals, and every manifest count agree. The authenticated coverage endpoint reports complete structured ingestion. This does not claim image-archive ingestion or exhaustive indexing of every raw text field.

Implementation follow-up: the importer and API are deployed on the VM. All 13 tables have reached their declared row counts. Ten deterministic storage tests cover provenance, literal FTS queries, timezone-equivalent filters, bounded/unresolved graphs, exact session relationships, and chronological context. A VM original-record read matched its stored SHA-256. Early timestamp precision differences were normalized in 50,466 derived index fields without changing source bytes. The index now resides on a dedicated 80 GB balanced persistent disk for ingestion and backup headroom; the original boot-volume copy is retained privately.

`/v1/context` returns actual adjacent source records: within a computer-use session, Claude SDK session, chat room, or table/agent scope. Event order uses `event_index`; other scopes use normalized UTC time with source-ID tie-breaking. Both context clipping and partial ingestion are disclosed. API counts are source-row counts: an event and its linked chat message may represent the same action and must not be summed as unique actions.

The SDK session audit found two duplicate `(agent_id, sdk_session_id)` groups. For ambiguous keys, the graph reports `SHARES_SDK_SESSION_KEY` edges to matching source rows and an ambiguity count instead of arbitrarily selecting an `IN_SDK_SESSION` parent. An agent ID is also not blanket authorship: goals are assigned to agents, sessions are run by agents, and SDK message streams contain human/tool/system rows. Edge labels preserve these distinctions.

Deterministic discovery now covers completed chat data only. The exact-repetition rule excludes clipped excerpts and normalized texts shorter than 80 characters, collapses whitespace, casefolds Unicode, and requires at least three identical normalized messages. It found 606 candidates among 174,355 eligible records out of 183,485 chat rows. A separate volume lens reports the largest known-agent message share in each room/UTC-day with at least 20 eligible messages (480 room-days); human and unknown speakers are counted separately and excluded from the denominator. Both lenses attach bounded canonical source-ID samples and explicitly set `causal_claim=false`. Neither measures failure, cooperation, quality, or influence. Pattern summaries are built offline and served from a small indexed table, rather than rescanning the corpus per UI request.


## Final validation

The metadata-only validation artifact is [data-validation.json](../docs/data-validation.json); the final HTTPS checks are [api-validation.json](../docs/api-validation.json). Original audit evidence and raw source records remain private on the VM. Thirty-seven samples spanning the first, middle, and last record positions of all tables matched their original JSONL SHA-256 hashes. No timestamps were missing or noncanonical, and no event index was missing or duplicated. This verifies sampled source slices, not a full reread and rehash of every original record.

The audit found **57 event-to-chat references without exported message rows**, **19 Claude Code messages without a matching session pair**, and **two ambiguous SDK session-key groups**. Every other checked reference resolves: turn/session, session/agent, chat/agent, chat/room, event/computer session, memory/agent, and individual goal/agent. These are export limitations, preserved as unresolved or ambiguous evidence rather than repaired by inference. The audit does not assert that every possible foreign key in the original schema was checked.

The SQLite main database is **9,985,875,968 bytes** with a zero-byte WAL after ingestion. The complete data directory, including private compressed originals and seek indexes, is 15,563,064,327 bytes. Indexed excerpts stay within 2,000 characters and selected metadata within 2,986 bytes (below the 8 KB cap). **820,359 excerpts are clipped**; **20,302 original records exceed the authenticated raw-view limit of 65,536 bytes** and therefore return explicitly marked prefixes through that endpoint. Neither search absence nor a clipped source view establishes absence in the full original.

All 46 backend fixture tests passed after the final investigator change. Deployed `app.py`, `store.py`, `assistant.py`, and `swarmtraces_adapter.py` hashes match the workspace exactly. Final HTTPS checks returned 401 for anonymous data requests; authenticated patterns, chronological context, original-record hash verification, and search returned 200. Measured searches took 0.090 seconds for `correction`, 1.089 seconds for the common term `the`, and 1.641 seconds for an absent probe term. These are individual post-ingestion checks, not throughput or concurrency benchmarks. Three direct Store searches returned in 0.066–0.084 seconds.

The full reference/field audit is an offline task and took substantially longer than interactive queries; its grouped aggregate used temporary disk sorting. It ran after ingestion, with no evidence-index writer. Full backup and isolated restore verification are coordinated separately by deployment, and should be read alongside this data audit before assessing recovery readiness.

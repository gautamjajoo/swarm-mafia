# Historical evidence API v1

Base path `/v1`; every `/v1/*` route requires `Authorization: Bearer <server token>`. API binds `127.0.0.1:8765`; `/health` returns only `{"status":"ok"}`. The frontend server proxies requests and keeps the token out of browser JavaScript.

Snapshot: `838b4150303ca8228e8edb432d8b8ccae353d258`.

Common success shape: `{snapshot, data, coverage, truncated, next_cursor}`. `coverage` reports each table's expected and indexed row counts and ingestion status; partial ingestion is always visible. Errors use an HTTP error status and `detail`.

All evidence routes accept `source=ai-village` (default) or `source=swarmtraces`. Unsupported filters return HTTP 400. Swarm Traces has no reliable agent identities or event timestamps; its timeline is unavailable. Its records use canonical `swarmtraces:R0000262` IDs and source-specific provenance. Upstream source failures return 502; bounded SQLite queries that exceed the five-second budget return 503.

## Routes

- `GET /v1/stats`: table coverage and index/search scope.
- `GET /v1/agents`: recorded agents with source IDs, names, model strings.
- `GET /v1/overview`: daily counts, action-type counts, explicit name-mention counts between agents. Mentions measure text matches, never influence. Overview may be cached briefly.
- `GET /v1/patterns?kind=exact_repetition&limit=10&source=ai-village`: offline deterministic chat-only candidates, limit <=30, kinds `exact_repetition` or `participation_concentration`. `data={kind,definition,qualification,built_at,inspected_chat_records,pattern_count,patterns}`. Repetition rows contain `{id,text,count,actor_count,first,last,source_ids<=10,unknown_actor_occurrences,evidence_status:'lexical_candidate',causal_claim:false,interpretation}`. Only nontruncated texts >=80 normalized characters occurring >=3 times qualify; normalization is Unicode casefold plus whitespace collapse. Volume rows contain `{id,room_id,day,agent_id,message_count,eligible_agent_messages,share,human_messages,unknown_agent_messages,unknown_speaker_messages,source_ids<=10,evidence_status:'volume_candidate',causal_claim:false,interpretation}`. Each room/UTC-day needs >=20 known-agent messages; denominator excludes human and unknown speakers, counted separately. This measures message volume, not influence, cooperation, or quality. Builds require complete chat ingestion; missing builds return 409. SwarmTraces is unsupported for these lenses. Source samples are bounded, not every matching record.
- `GET /v1/search?q=...&agent_id=...&table=...&from=...&to=...&limit=30&cursor=0`: bounded FTS phrase/token search of indexed excerpts (not full raw content); filters are optional. `limit` <=100. Empty query lists latest records. Cursor is a numeric offset; best used within a stable snapshot/coverage state.
- `GET /v1/timeline?agent_id=...&from=...&to=...&limit=100&cursor=0`: same record shape, chronologically ordered, limit <=200.
- `GET /v1/records/{table}/{source_id}`: a single indexed record and exact source pointer.
- `GET /v1/records/{table}/{source_id}/raw?source=ai-village`: exact original JSONL record, at most 65,536 source bytes, via the private gzip seek index. Returns `data={id,raw_json,bytes_returned,record_bytes,hash_verified,format,provenance}`. Oversized records have `format=jsonl_prefix`, `truncated=true`, and are not valid complete JSON. A full row verifies its SHA-256; a truncated prefix has `hash_verified=false`. Returns 409 until that table's seek index is ready. This is an authenticated evidence-inspection response, not a bulk export.
- `GET /v1/graph?seed=chat_messages:UUID&hops=1&limit=100`: exact recorded relationships only, hops <=2, nodes <=200; `data={nodes,edges}`. A graph can be seeded from any record ID. Agent ID uses `agents:UUID`.
- `GET /v1/context?seed=table:UUID&before=8&after=8&mode=source`: recorded neighboring records, up to 25 before and 25 after plus seed. `data={seed,records,scope,before_truncated,after_truncated,interpretation}`. Default source scope is same computer session for turns, same `(agent,sdk_session)` for Claude Code messages, same room for chat messages, otherwise same table and agent (table-only when actor unavailable). Events order by canonical `event_index`; other rows by normalized UTC timestamp with source ID/table tie-breakers. Optional explicit `mode=actor` spans tables for the same recorded/session-joined agent, ordered by UTC and clearly labeled `actor_across_tables`; unavailable actor identity returns 400. Return scope/coverage/clipping explicitly; sequencing is not causality. AI Village only.

## Record

```json
{"id":"chat_messages:UUID","source_id":"UUID","table":"chat_messages","agent_id":"UUID","timestamp":"2026-01-02T12:00:00.123456Z","action_type":"AGENT_TALK","excerpt":"bounded source text","excerpt_truncated":false,"metadata":{},"evidence_status":"recorded","provenance":{"snapshot":"revision","object_uri":"gs://bucket/ai-village/chat_messages.jsonl.gz","generation":"generation","line":123,"sha256":"hash of original JSONL line bytes","byte_offset":456,"byte_length":789}}
```

Metadata is bounded to 8 KB and excerpts to 2,000 characters. Search indexes selected excerpts only, including action text and the beginning of textual content; absence from search is not absence from the corpus. Raw provider responses are preserved in private original compressed files on the VM; exact byte pointers permit later retrieval with a gzip seek index. No bulk raw-content route is exposed.

Where a source agent ID resolves, records also contain `actor_name` and `actor_name_provenance={source_record_id:'agents:UUID',field:'name',join,meaning}`. This is the exported display name of the associated agent; it does not convert SDK user/tool/system rows into agent-authored messages. Turns include `actor_provenance` for the exact session-to-agent join.

Pattern rows add display names through exact source ID lookups: concentration rows have optional `agent_name`/`room_name`; repetition rows have up to ten `actor_names` with `actor_names_scope` and `actor_names_truncated`. Pattern evidence samples span up to five earliest and five latest matching records by UTC/source-ID ordering, stated in `sample_selection`; qualification rules and counts are unchanged.

Graph edges: `{id,source,target,type,evidence_status:"recorded",provenance:{source_record_id,field}}`. Implemented types: `AUTHORED_BY` (chat/memories), `RAN_BY` (sessions), `ASSIGNED_TO` (individual goals), `ASSOCIATED_WITH_AGENT` (events/SDK message streams), `IN_SESSION`, `IN_ROOM`, `HAS_MESSAGE`, `IN_SDK_SESSION`, `IN_VILLAGE`. An SDK stream includes user/tool/system messages, so its agent association is not blanket authorship. Turn→agent attribution is shown through the session, since the turn does not directly contain an agent ID. Edges express source fields, not causal influence. Missing parent rows stay unresolved and are not fabricated. Responses cap nodes at 200 and edges at 600 and explicitly disclose truncation.

Timestamps are UTC. `event_index` in event metadata is the canonical event ordering; chronological order across other tables does not prove causality. Summaries carry `evidence_status:"secondary_generated"`.

Two exported SDK session-key groups are ambiguous. Those joins use `SHARES_SDK_SESSION_KEY` rather than selecting an arbitrary `IN_SDK_SESSION` parent; graph `ambiguous_references` reports encountered ambiguous references.

Counts are source-record counts, not unique actions. `events` and their referenced `chat_messages` can describe the same action. Context and search preserve both provenance records and disclose this in `coverage.counting_unit`.

The assistant module may add authenticated `/v1/investigate` separately. Its statements must cite record IDs and distinguish observations, hypotheses, and counterevidence.

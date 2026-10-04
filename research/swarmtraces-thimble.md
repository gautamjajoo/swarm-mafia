# Swarm Traces and Thimble: ingestion and implementation findings

Inspected 2026-10-04. Thimble pinned to commit `6cee6e02b3a384bdf0e56c9e7b639ad9ad634635` in a read-only clone at `/tmp/thimble-source-review`. No project scripts, installation commands, or captured payloads were executed. No AI Village data was downloaded.

## Recommendation

Build two different adapters. **Swarm Traces supplies real published incident artifacts and decoding ancestry**, suitable for evidence exploration and content-based hypotheses. **Thimble supplies reusable source code and small bundled sample formats**, useful for citation handling, multi-agent UI patterns and adapter regression fixtures. Do not market Thimble's samples as verified real-world trajectories. Do not convert a Swarm Traces artifact's recovered text, identifier, or parent into an invented message, actor identity, or agent handoff.

For the first product demonstration, the checked-in Swarm Traces sample provides seven actual records, including one explicit parent–child pair. Show a source badge, provenance, captured text, redaction markers, and a decoding graph. Keep any behavioral classifications visibly separate from source observations.

## Accessible Swarm Traces interfaces

The [report](https://swarmtraces.org/) links its [evidence viewer](https://swarmtraces.org/viewer/) and [gzip JSONL release](https://swarmtraces.org/data/final/redacted.jsonl.gz). The viewer's [JavaScript](https://swarmtraces.org/viewer/viewer.js) documents these same-origin GET interfaces; direct requests were verified:

| Interface | Purpose / tested details |
|---|---|
| `/api/meta` | Counts, release build timestamp, archive byte count/SHA-256, kinds, tags, placeholder families, roots, search capabilities. |
| `/api/search?q=HELLO&mode=literal&ci=1&limit=3` | `items`, `next_cursor`, `complete`, `scanned`, `elapsed_ms`; use returned cursor, not guessed offsets. |
| `/api/search?...&kind=recovered_text` | Kind filter; viewer also supplies `roots=1`, repeated `tag`, and modes `words`, `literal`, `regex`. |
| `/api/row/R0000028` | Full `row` plus ancestors, children, child-pagination flag and siblings count. |
| `/api/row/{id}/text` | Viewer-advertised exact text download; prefer JSON endpoint for structural provenance. |
| `/api/row/{id}/children?offset=N` | Viewer-advertised child pagination. |
| `/viewer/#/row/{id}` | Human-readable deep link. |

No authentication was needed. Python's default user agent received HTTP 403 for the viewer; `Mozilla/5.0` worked. An HTTP HEAD of the archive returned 501, while a GET with `Range: bytes=0-16383` returned 206 and a valid compressed prefix. These are observed operational details, not a promised API contract. Avoid treating failed HEAD as missing data. Use bounded GETs, a modest request rate and explicit timeouts; do not use regex enumeration for bulk ingestion.

[Metadata](https://swarmtraces.org/api/meta) observed:

- Build: `2026-09-29T18:56:52Z`.
- 189,579 rows: 91,037 `payload`, 75,534 `recovered_text`, 23,008 `response`.
- 128,454 roots; 30 tags; 65,219,859 text bytes.
- Archive: 15,214,685 bytes; SHA-256 `7b66ab21674de52fcd3f557652f68b1801170c998e2f266862124e6edf283488`.
- Global `time_span.min` and `.max` are null. All inspected records have null `time_utc`.
- Full-text search enabled; the API advertises a 12-second regex budget.

Counts are release metadata, not agent counts, successful attacks, unique actions, or complete execution traces.

## Exact observed schemas

The **original archive** prefix has these seven keys:

```typescript
type ArchiveRow = {
  id: string;           // R0000001
  cite: string;         // R0000001:865502a6
  kind: string;         // payload | recovered_text | response in current metadata
  parent_id: string | null;
  time_utc: string | null;
  tags: string;         // empty string in inspected original prefix; not an array
  text: string;
};
```

Do not assume the API and archive are identical: archive tags were a string, while API tags are an array. Nonempty archive-tag encoding was not established from the small prefix; preserve `tags_raw` until the delimiter/encoding is verified, or use API tags for selected records.

The **API row** is:

```typescript
type ApiRow = {
  id: string; cite: string; kind: string;
  parent_id: string | null; root_id: string; depth: number;
  time_utc: string | null; tags: string[];
  text_len: number; n_children: number; n_placeholders: number;
  source: string;        // "rows" in inspected records
  text: string;
};
type RowEnvelope = {
  row: ApiRow;
  ancestors: RelatedRow[];
  children: RelatedRow[];
  children_more: boolean;
  siblings: number | null;
};
```

Search items omit full text and return `snippet` with `before`, `match`, `after`, character `offset`, and clipping flags. Related-row summaries can mark `missing`; missing parents must remain explicit dangling references rather than disappear. Preserve source `cite` as an opaque identifier; its suffix looks hash-like but the algorithm was not verified. Add your own SHA-256 of exact bytes.

Recommended normalized artifact:

```json
{
  "id": "swarmtraces:<release-sha256>:R0062529",
  "source_record_id": "R0062529",
  "source_cite": "R0062529:80e64da3",
  "record_type": "artifact",
  "artifact_kind": "recovered_text",
  "parent_source_record_id": "R0000262",
  "root_source_record_id": "R0000262",
  "occurred_at": null,
  "actor_id": null,
  "provenance": {
    "url": "https://swarmtraces.org/api/row/R0062529",
    "viewer_url": "https://swarmtraces.org/viewer/#/row/R0062529",
    "raw_object_sha256": "a791a85f5139b4e4e4b40b00217b81462a4c409c32cc0f473971acc90ac7d4f1"
  },
  "redacted": true
}
```

Include ingestion timestamp, source release hash, byte/line locator, adapter version and original JSON in storage; the example omits those runtime-specific fields for clarity.

## Graph and extraction boundaries

1. **Observed ancestry:** `R0062529.parent_id = R0000262` supports `recovered_from(R0062529, R0000262)`. Label it decoding/recovery ancestry, not agent communication or execution causality.
2. **Root grouping:** `root_id` groups artifacts; detect cycles and unresolved parents when computing roots from archive rows. Do not use row IDs as chronology.
3. **Tags:** represent source tags as annotations with their provenance. Tag co-occurrence is not collaboration.
4. **Redaction placeholders:** index exact placeholder strings as opaque text mentions. Repeated numbered placeholders can support a candidate relationship within a release; no claim that distinct markers identify distinct real people. Generic markers such as `[REDACTED SENSITIVE CONTENT]` cannot be meaningful entity joins.
5. **Actor mentions and URLs:** retain span-level mentions with a nullable resolved identity and an extraction method/confidence. Never dereference captured URLs. Names in scripts are asserted aliases, not verified identities.
6. **Outcome:** a `payload` demonstrates recovered content; it does not establish execution or success. `response` should also retain provenance and linkage limits. Behavioral summaries should say “attempted” or “contains code for” unless independent evidence supports completion.

The [report's limitations](https://swarmtraces.org/#limitations) describe predominantly outbound artifacts, incomplete reconstruction, sparse native timestamps, unreliable self-chosen aliases, uncertain origin for some records, and unconfirmed execution outcomes. The release redacts sensitive material and omits undecoded blobs. These limitations belong in dataset metadata and result wording, not only a buried disclaimer.

## Small source corpus actually saved

All source samples are under `research/source-samples/`:

- `swarmtraces/archive-prefix-3.jsonl`: first three complete, unmodified JSONL records from a 16 KiB HTTP range; 2,261 bytes. Full archive was not downloaded.
- `swarmtraces/R0000028.json`, `R0000235.json`: short HELLO test artifacts.
- `swarmtraces/R0000262.json`, `R0062529.json`: one payload and its recovered-text child; useful for lineage checks. These contain command text and must stay inert.
- `swarmtraces/api-rows.jsonl`: convenience projection of those four API envelope `row` objects; derived file, not the original release schema.
- `swarmtraces/meta.json`, `robots.txt`, `manifest.json`: retrieval metadata, URLs and SHA-256 hashes.
- `thimble-fixtures/roster.csv`, `help-desk.jsonl`, `Welcome.jsonl`, `LICENSE`, `manifest.json`: tiny bundled software samples and their source paths/commit/hashes.

No sampled payload was run. Safe handling means a bounded data-only parser, escaped text rendering, disabled automatic link fetching, and no `eval`, shell interpretation, notebooks or custom generated viewers over source text. A security scan can inspect strings without invoking them. For later full ingestion, stream gzip JSONL with a decompressed-byte limit, maximum record length, row-level parse errors and immutable original bytes.

## Rights and access

No explicit Swarm Traces dataset license was found on the report or viewer during inspection. Its download being public does not establish redistribution, commercial rehosting, or model-training rights. Track `license_status: unknown`, retain source attribution, and resolve rights before distributing the full corpus in a commercial service. This is an unresolved source-rights question, not a claim that the data is prohibited.

The retrieved [robots.txt](https://swarmtraces.org/robots.txt) explains `search`, `ai-input` and `ai-train` content-signal semantics but contains no actual Content-Signal assignment, User-agent rule or Disallow rule. That absence is neither an explicit license nor an AI-training grant. Saved bytes allow later comparison.

[Thimble's LICENSE](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/LICENSE) is Apache-2.0. Retain the license and relevant attribution/notices when reusing source, mark modifications, and inspect dependency licenses for bundled redistributions. This does not license unrelated incident data. The repository is an alpha research prototype; pin a commit rather than inheriting main's changes silently.

## Thimble patterns worth adapting

### Source-linked evidence and validation

[`backend/app/refs.py`](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/backend/app/refs.py) defines locators for JSONL/text lines and ranges, message blocks, character spans, SQLite rows, JSON pointers, CSV rows, PDF pages, tool calls, report paragraphs, notebook outputs and custom views. Separate stable source identity from UI location. Character spans use UTF-16 code units; a Python code-point offset must be converted before highlighting in JavaScript.

[`backend/app/heal.py`](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/backend/app/heal.py) offers deterministic value-to-output citation checks, distinguishing linked, unresolved and contradicted claims. A citation is moved only when a unique supporting location is found. Our product should retain a correction audit trail and preserve analyst text rather than silently giving an unsupported number a plausible source.

[`backend/app/ledger.py`](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/backend/app/ledger.py) supplies atomic temporary-file replacement, append logs, boot IDs and per-log sequences. Reuse these ideas for resumable ingestion and immutable evidence manifests; a hosted concurrent service will still need transactional storage.

### Multi-agent shared-artifact reader

[`multiagent-swimlane/reader.py`](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/extensions/multiagent-swimlane/cards/multiagent-swimlane/reader.py) accepts CSV/JSONL and maps aliases for actor, place, timestamp, text, record ID, revision, reply and goal. It recognizes roster rows, chat posts, full wiki snapshots and page indexes. Useful implementation details include source-line citations, malformed-record reporting, duplicate detection, timestamp normalization, lazy text loading and revision diffs.

Its links have very different epistemic strength: `reply` derives from an explicit reply field; `names` links to the latest prior record by a mentioned account; `same place` links adjacent activity by different accounts. Preserve those as separate edge classes. A textual mention or shared place must not be called a verified handoff. Do not copy case-insensitive actor merging into a production adapter unless that source guarantees case-insensitive identity.

The [card schema](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/extensions/multiagent-swimlane/cards/multiagent-swimlane/card.json) has `actions[{ref,summary,thread?}]`, inferred `goals{account:text}`, and `links[{from,to,type}]`. It is a good compact analyst-selected story view; use a separately complete graph index for exploration. Label inferred goals and analyst-defined links explicitly.

### Session/tool-call adapter

[`plugin/viewers/linked-sessions/reader.py`](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/plugin/viewers/linked-sessions/reader.py) describes a concrete Claude-style JSONL family:

- Lead at `runs/<run>/<session-id>.jsonl`; subagents at `runs/<run>/<session-id>/subagents/agent-<id>.jsonl`.
- Record keys `type`, `uuid`, `parentUuid`, `timestamp`, `message{role,content}`, optional `toolUseResult`.
- Content blocks `text`, `tool_use{id,name,input}`, `tool_result{tool_use_id,content,is_error}`.
- `sessions-index.json` supports both v1 `sessions` and v2 `entries` metadata.
- Exact `tool_use.id` / `tool_result.tool_use_id` match gives a call-result edge. Task results' `agentId` support a spawn edge. Parent-message UUID supports conversation ancestry.
- The reader tolerates `Agent` versus `Task`, `isError` versus `is_error`, duplicate UUIDs, incomplete JSONL tails and missing index entries. It treats actual transcript files as authoritative over the index.

Its fallback spawn matching by result text or prompt equality is useful candidate generation, but production should retain `link_basis` and confidence rather than merging these with explicit agent-ID joins. Keep malformed/missing-time records in a quarantine table, not silently discard them from the evidence inventory.

### Do not deploy its local trust model unchanged

The [README](https://github.com/safety-research/thimble/blob/6cee6e02b3a384bdf0e56c9e7b639ad9ad634635/README.md) describes a localhost research workbench with no server login and notebook network access. For a production shared service, use authenticated tenant isolation, read-only source stores and separate restricted analysis execution. Import only the citation/parser/view concepts needed; do not install the Claude plugin or run arbitrary custom reader/viewer scripts as the ingestion path.

## Concrete implementation order

1. Implement `swarmtraces_api_v1` against the four saved envelopes and `swarmtraces_archive_v1` against the three original rows; reject shape assumptions that conflate API tags and archive tags.
2. Store a source-version manifest keyed by archive SHA-256, raw artifacts, normalized records, explicit ancestry edges and annotation/mention tables separately.
3. Provide source deep links and exact local text spans for every derived claim; show missing timestamps and unresolved actors as unknown.
4. Test ID stability, exact text preservation, parent/child resolution, duplicate source ingestion, dangling references, and escaped script-like content. A repeat import should create no duplicate records or edges.
5. Add a separate Claude-session adapter using explicit tool-call IDs and agent IDs, borrowing the linked-session schema handling. Use Thimble samples only as labeled fixtures until a verified operational corpus is supplied.
6. Resolve Swarm Traces redistribution rights before full public hosting; cache only the small research sample for this stage.

# Independent quality and trust-boundary review

Reviewed 4 October 2026. Read-only inspection of the in-progress backend, clients, deployment configuration, product API routes, and product specification. No backend or product code was changed. Files are being edited concurrently; line references identify the inspected implementation and fixes need a fresh check. This is not a penetration test or a production security certification.

## Main result

The architecture has useful controls: authenticated backend reads, parameterized SQLite access, bounded returned records, exact quote matching, explicit historical-evidence instructions, fixed upstream domains, and no execution tools in the investigator. The main correctness risk is that scope and evidence limitations can be lost between retrieval and analysis. Quote matching establishes that quoted text exists; it does not establish that the accompanying claim is supported or that a historical intervention worked.

**Concurrent-fix update:** A subsequent read confirms endpoint source routing now uses `source_store`, all frontend data/persistence routes check `signedIn`, and investigator records preserve excerpt truncation/metadata and source coverage. Repeating the in-memory probe confirmed `truncated=true`, `excerpts_truncated=true`, preserved partial-index coverage, and rejection of the invalid-type/causal claim. Accepted claims now have a `quote_matched_semantic_support_unverified` validation label. These are code/probe checks, not deployed auth validation or proof of general semantic validation. The findings below preserve the original reviewed behavior so their rationale and acceptance criteria remain useful.

## Current status after final product review

The numbered Q findings below record the initial review; they are not all open defects. Current code inspection confirms these changes:

| Finding | Current status |
|---|---|
| Q1 source routing | Addressed in code through source adapter selection. |
| Q2 coverage/truncation | Addressed in code and the repeated in-memory probe. |
| Q3 quote/claim distinction | Explicit AI-draft and semantic-support-unverified labels; enum validation and conservative causal-language rejection added. General semantic correctness remains unverified by design. |
| Q4 timestamp bounds | UTC normalization added; data agent reports five passing tests. This reviewer inspected the normalization code but did not rerun those tests. |
| Q5 work bounds/pruning | SQLite five-second progress-handler budget, overview pruning disclosure, and SwarmTraces overall graph deadline/worker bound are present in current code. Deployment load behavior was not independently tested. |
| Q6 authorization | Every frontend data/persistence route now checks the injected identity header. Private dispatcher integrity and header non-spoofability still require deployed verification; header presence alone is not cryptographic authentication. |
| Q7 export trust | Browser JSON exports carry an explicit untrusted-data declaration; pin source and excerpt-truncation fields persist. Saved analysis currently removes full retrieved source objects to bound storage; exact quotes remain. CLI detached-export trust wording should still be checked separately. |
| Q8 corrections | Resolved by the intentional notes model: persisted counterevidence/disputed notes become the next request's corrections. A separate corrections field is unnecessary. Challenge reasons precede referenced model text; backend correction budget is now 1,500 characters. |

### Final product re-review: reported fixes verified in code

All five material issues from the preceding product pass are now addressed in the inspected source. These are independent code-verification results, not claims that this reviewer reran the root's browser tests. Line references below identify the re-review snapshot; formatting or subsequent edits may shift them. No product changes were made by this reviewer.

| Previously reported issue | Verified implementation |
|---|---|
| Restore/pattern stale-result race | `openSaved` checks investigation, open, evidence, and selection generations before source-view writes (`product/app/page.tsx:704–711`). `openPattern` checks the corresponding investigation/evidence/selection tokens before applying its sample (`388–407`). |
| AI/context completion overwrites newer evidence | `ask` captures the evidence epoch (`464–465`), checks it before populating records, and uses a functional update that retains a nonempty current list (`523–524`). `surrounding` captures and checks both evidence and selection epochs (`349–367`). |
| Draft leakage across cases/sources | `clearDrafts` resets question, note text/target/type, study, dialogs, raw preview, graph seed, and pattern state (`564–575`). Reset and saved-case restore call it (`591`, `679`). Record-level context/challenge clears the old target/text (`1801–1802`). |
| Timeline/actor-context restore mismatch | Workspace serialization saves `context_mode` and tab (`201–213`); the schema includes the mode. Restore passes the saved context mode (`748`) and uses the timeline endpoint for saved timeline views (`755–768`). |
| Study limits make cases unsavable | Field `maxLength` values match schema bounds (`2491–2497`); count limits are checked in both button state and insertion handler (`2515–2528`); proposals can be removed (`2314–2322`). |

The root is running browser verification for these flows. No previously reported frontend issue remains marked open on the basis of an obsolete code snapshot.

**Context-anchor fix verified at product commit `82126c60557e0aa3d8543888b325dbf4f539364b`:** `context_seed` is serialized independently from `selected_id`, accepted by the persistence schema, and used for context restoration with a compatibility fallback to selection. The previously reported A-anchor/B-selection mismatch is resolved. Root reports a context/correction round-trip test, five schema checks, five local persistence checks including optimistic 200/409, and desktop plus 390px-mobile validation with no horizontal overflow. Those execution results are attributed to root; this reviewer independently inspected the code.

### Latest incremental review at commit 82126c

- **Stop analysis:** Verified browser AbortController wiring and generation invalidation. A late response is discarded, the question is restored, and the notice correctly states that a dispatched server/model request may still complete. This is client cancellation, not a claim of server-side cancellation.
- **WebMCP failures:** Verified that an undefined action result now throws an explicit incomplete/interrupted-operation error instead of returning apparent success.
- **Inline human review:** Notes render next to their target claim and remain eligible for subsequent-request corrections. The narrow identity issue found in this pass was corrected and rechecked below.
- **No product mutations:** Only this review document was updated.

Two concrete P2 interactions were found at that commit, then fixed in the working tree and independently rechecked:

1. **Context with a closed inspector — resolved in code:** The context-restore branch now accepts `s.state.context_seed || s.state.selected_id` (`product/app/page.tsx:765–767`). A context window can therefore restore even when its inspector was closed before saving. Root is performing the corresponding browser check.
2. **Identical text across different evidence — resolved in code:** Inline notes now match both claim text and source-ID count/membership (`product/app/page.tsx:1956–1959`). A challenge to a claim about one source set no longer appears under an identically worded claim about another source set.

No material frontend issue reported by this review remains outstanding in the latest inspected working tree. This is a bounded review conclusion, not a claim of exhaustive correctness; deployed behavior remains covered by root's separate browser/auth validation.

### Accepted product scope decision

Defer a third aggregate name-mentions graph until each edge can open its exact matching messages and surrounding context. Existing aggregate `overview.agent_mentions` counts are useful for discovery, but are not communication, readership, influence, or causal edges. A future lens should say “Author mentions agent name,” preserve the explicit matching/count rule, show excerpt/index coverage and top-edge truncation, and support source drilldown. Current recorded-relationship graphs plus repetition/participation candidates and source investigation remain the focus.

No additional confirmed public-auth bypass was found in this static product pass. Deployment checks belong to the root's ongoing validation. Previous source-selector crash, dropped AI date filters, wrong selected-record priority, editable-query pagination, and missing dirty tracking for date changes were corrected in the inspected implementation.

### Q1 · P1 · Requested source can be silently ignored by investigation

**Evidence:** `clients/observatory_client/api.py:164` places `source` in `context.filters`. In the inspected `backend/assistant.py`, `FILTER_KEYS` omits `source`, and `investigate_endpoint` always instantiates the AI Village `Store(path)`.

**Impact:** A request explicitly selecting SwarmTraces can produce an AI Village investigation. A source chip in the UI can therefore contradict the evidence used. This is an integrity issue even if individual citations are real.

**Required behavior:** Resolve the source once at the authenticated endpoint; reject unsupported source values; pass the corresponding retrieval adapter; echo the canonical source and snapshot in context and coverage. Never silently fall back between corpora.

**Verification:** For a SwarmTraces request, assert that AI Village Store methods are never called; all retrieved records identify the selected source. Test unknown source, missing database, and valid SwarmTraces operation when no AI Village database is configured.

**Coordination status:** Reported to root and investigator agent; source-routing changes are in progress. Do not mark fixed based solely on this review.

### Q2 · P1 · Analysis discards material source coverage and truncation

**Evidence:** `backend/assistant.py:_record` truncates excerpts to 1,600 characters and discards `excerpt_truncated` and metadata. `retrieve` checks `next_cursor`, but does not retain upstream `coverage`, `snapshot`, or `truncated`. `finish` creates a new coverage object describing only its own record/call limits. The upstream `Store` and SwarmTraces adapter provide richer limitations that are lost.

**Confirmed probe:** An injected in-memory store returned one excerpt with `excerpt_truncated=true`, `coverage.complete=false`, `indexed_records=1`, `expected_records=100`, `truncated=true`, and `next_cursor=null`. The investigator returned `coverage.truncated=false`, no ingestion counts, and a 1,600-character source with no truncation marker. Graph truncation was also true in the fixture and was lost.

**Impact:** The analyst and model cannot distinguish a complete short record from a clipped excerpt, or sparse indexing from a broad search. Negative claims about correction uptake and missing handoff context become especially easy to overstate.

**Required behavior:** Preserve source-specific coverage alongside investigation-budget coverage; OR together explicit truncation signals; flag excerpt shortening at every stage; preserve snippet/raw-text distinction and graph unresolved-reference counts. Include these limitations in the model payload as well as the returned response. Search result absence must remain “not found in inspected excerpts.”

**Verification:** Test a partial index with no pagination cursor, clipped search snippet, graph truncation without a next page, an excerpt shortened by the investigator, and a model-budget eviction. Each must have a visible, machine-readable reason.

### Q3 · P1 · Quote validation can make an unsupported causal claim look like an observation

**Evidence:** `backend/assistant.py` accepts a finding when its IDs exist and each cited quote is a substring. It does not check semantic support. An unrecognized `evidence_type` defaults to `observation`.

**Confirmed probe:** A deterministic fake model emitted “The intervention caused a 90% improvement.” with the real quote “Agent requested the review twice.” and `evidence_type="not-a-valid-type"`. The result was accepted and labeled `observation`.

**Interpretation:** This verifies the validation boundary, not the frequency of such output from the configured live model. A system prompt is useful, but this probe means the API must not describe accepted findings as verified conclusions.

**Required behavior:** Reject unknown evidence-type values. Mark output `AI draft`, `quote_match_validated`, and `semantic_support_unverified`; historical causal explanations remain hypotheses. Keep proposed studies separately tagged unexecuted. If an entailment check is added, retain its fallibility and reviewer disposition rather than turning it into proof. Causal/effect claims need linked executed-study evidence, which this historical investigation path does not currently supply.

**Verification:** Include unrelated valid quotes, negated statements, quotations of another agent's claim, superseded instructions, and secondary summaries. Confirm that no validation badge means more than the actual check. Human review can dispute or correct every generated finding.

### Q4 · P2 · Timestamp scope accepts timezone values but compares text

**Evidence:** `backend/store.py:112–122` compares timestamp TEXT lexicographically. `backend/ingest.py:27–31` retains existing timezone offsets. The client accepts timezone-aware ISO timestamps without converting them to UTC; direct API parameters have no timestamp validator.

**Impact:** `from=2026-10-01T02:00:00+02:00` can exclude a record at `2026-10-01T00:00:00Z`, even though they are the same instant. Mixed precision/offset forms can also affect ordering. A chronology-based behavioral conclusion then uses the wrong scope.

**Required behavior:** Validate and normalize bounds and indexed timestamps to one UTC representation or compare numeric instants; reject inverted bounds. Keep missing timestamps explicitly outside time-filtered results and disclose the exclusion. Preserve canonical event indices for source-order inspection where available.

**Verification:** Equivalent instants in Z and offset notation produce identical result sets; malformed/inverted bounds fail clearly; unknown timestamps never acquire fabricated chronology.

### Q5 · P2 · Some output bounds do not bound work or disclose pruning

**Evidence:** `backend/store.py:133–140` caps action types at 80 and mentions at 300 while returning the default `truncated=false`. SQLite queries have an output limit but no query progress/deadline budget. `backend/swarmtraces_adapter.py:244` permits up to 24 upstream reads, each with a 12-second socket timeout, without an overall graph deadline. `asyncio.to_thread` timeout does not cancel the underlying synchronous operation.

**Impact:** Overview counts can appear exhaustive when categories/relationships are omitted. Slow authenticated search/graph calls can occupy server workers longer than the frontend timeout, and repeated cancelled requests can leave work running.

**Required behavior:** Return per-aggregation truncation and limits; add bounded query execution and an overall upstream budget; bound concurrency for expensive routes. Cancellation should terminate work where the storage/transport supports it. Preserve already retrieved evidence on timeout with an explicit incomplete state where appropriate.

**Verification:** Use a fixture with more than 300 mention pairs; verify the omission signal. Inject slow upstream requests and expensive SQLite queries; confirm maximum elapsed work and concurrency rather than only response timeout. No production load test was performed during this review.

### Q6 · Deployment gate · Frontend API authorization depends on the private Sites perimeter

**Evidence:** The inspected `product/app/api/evidence/[...path]/route.ts` forwards its configured shared bearer token without calling `requireChatGPTUser`. Investigation read/write routes similarly have no application identity check. `product/lib/server.ts:writeGuard` rejects a mismatched Origin but accepts missing Origin; this is not authentication. Backend `app.py:27–34` does require a token, and Caddy also gates the upstream proxy.

**Impact condition:** If every frontend route and worker alias is protected by the private hosting perimeter, the application may intentionally use workspace-level access. If any API route or direct worker URL is reachable outside that boundary, it becomes a credentialed proxy and investigation-write surface. No public exposure was demonstrated.

**Required verification before describing the workspace as private:** An unauthenticated GET to every API family and an unauthenticated POST/PUT, including requests without Origin and any direct worker alias, must be denied by the deployed perimeter. Confirm auth identity headers cannot be supplied by callers. Define whether all workspace members intentionally share all saved investigations. Do not imply per-user isolation: current database queries do not enforce it.

**Additional bound:** The FastAPI 40 KB investigation check occurs after JSON parsing. Frontend `smallBody` has a streaming limit, but direct authenticated backend access needs an ingress body limit as well. A 413 after parsing is not a memory bound.

### Q7 · P2 · Export and source trust labels should travel with the evidence

**Evidence:** The CLI serializes JSON rather than shell commands or HTML, and the client export preserves query, limitations, and the backend envelope. These are good defaults. `LIMITATIONS` does not currently include an explicit instruction that source excerpts and metadata are untrusted data. MCP server instructions carry that warning, but detached JSON consumers do not necessarily receive it. Saved pins accept caller-provided excerpt/provenance objects.

**Impact:** A downstream coding agent may ingest a packet outside the original MCP context and mistake embedded source instructions for directions. A caller can also alter a saved pin's text/provenance; persistence alone cannot make that pin a server-verified quotation.

**Required behavior:** Include packet-level and per-source trust labels; separate source text from analyst instructions; label caller-submitted pin text as user supplied until checked against its exact source version/hash/span. Export exact original provenance and hash basis. Preserve the distinction between SwarmTraces search-item hashes and full-row hashes. Use JSON/text downloads by default; if Markdown is added, escape source content and prevent it from creating active HTML, auto-fetched images, or task directives. Never create executable files from trace commands.

**Verification:** Export records containing shell-looking text, Markdown fences, HTML, image URLs, and “ignore prior instructions.” The exported structure must remain valid data, source text must not execute or fetch resources, and trust labels must survive a round trip through CLI/MCP and saved investigations. Test that modified pin text cannot acquire a “source verified” badge.

### Q8 · Resolved design clarification · Corrections persist through notes

The initial review identified that an arbitrary `state.corrections` key would be stripped by the schema. The implemented product does not use that key: human challenges are persisted as `notes[]`, including their target claim/source references, and the next AI request derives corrections from counterevidence/disputed notes. That is a valid persistence contract and requires no duplicate correction array.

**Verification still needed:** Add a challenge, save, reload, and submit a follow-up: the reason and target references must remain in saved notes and reach the investigator within its declared budget. Challenge text, clipping, and omitted older notes should be distinguishable. The notes are not a full authorship/revision audit trail.

## Observed fixes and controls worth preserving

- The investigator agent has added `_in_scope` checks before evidence enters `sources`; this addresses the initially observed explicit-ID filter bypass. Recheck record IDs, graph hydration, and malformed timestamps together after source routing lands.
- Backend authentication fails closed when no token is configured; constant-time comparison is used. `/health` exposes only a status value.
- SQLite is opened read-only and `query_only` is enabled. FTS uses literal tokens and parameterized values. No caller-supplied SQL is executed.
- SwarmTraces uses fixed official API paths, row-ID validation, response byte caps, a bounded cache, and restricted redirect destinations. Recovery ancestry is explicitly distinguished from communication; no actor roster or timeline is invented.
- Investigator evidence is placed in `UNTRUSTED_EVIDENCE`, with instructions to ignore embedded commands, and has no shell/action tools. This reduces available impact but does not by itself demonstrate resistance to misleading synthesis.
- Model output IDs and exact quote substrings are checked; invalid citations are rejected; proposed tests carry `proposed_not_executed`; model failures do not produce fabricated replacement findings.
- Client credentials come from configuration, redirects are disabled, remote plaintext HTTP is rejected, and raw backend error bodies are not echoed. Keep these properties as CLI/MCP capabilities grow.

## Minimal acceptance sequence

1. Correct source routing and preserve scope/coverage through the investigator.
2. Run deterministic tests for quote-match-only claims, invalid evidence types, injection payload transport, and clipped/incomplete evidence.
3. Verify equivalent timestamp bounds and overview truncation.
4. Verify deployed unauthenticated access denial at the frontend and backend, and bounded body/query/graph work.
5. Export and reopen one investigation containing support, counterevidence, an unresolved dispute, and a proposed study. Check every citation, hash basis, source snapshot, and untrusted-data label.

Do not report these checks as passed until executed against the final implementation. The two in-memory investigator probes above were executed; other checks are specified follow-up verification.

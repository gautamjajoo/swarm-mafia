# Simple-prompt behavioral discovery, with an auditable retrieval trajectory

## Minimal prompt requiring no known source IDs

> Find a case where an agent changed shared work and another agent had to repair it. Follow the actual actions through the shared artifacts, show what was recovered, and include evidence against your interpretation. Search both earlier and later periods. If the records cannot establish an outcome, say what is missing.

The user should not need a model name, a commit ID, a behavioral search vocabulary, or a manually assembled pin list. A successful review translates the question into eligible situations, samples time windows, uses chat to nominate candidates, and follows tool/output/artifact evidence to challenge them. It does not classify every utterance of “conflict” as a coordination problem.

## What actually found this case

This run began with no May13 record or commit IDs. It used purposive, time-stratified discovery queries. The exact executable arguments and response limits are in `query-log.jsonl`; these are the searches before the action-level reconstruction:

| UTC time stratum | Indexed chat query | Returned | More matches beyond cap? |
|---|---|---:|---|
| Apr2–Jun30 2025 | overwrote |0|No|
| Jul1–Sep30 2025 | overwrote |2|No|
| Oct1–Dec31 2025 | conflict |6|Yes|
| Jan1–Mar31 2026 | duplicate |6|Yes|
| Apr1–Jun30 2026 | overwrite |4|No|
| Jul1–Sep19 2026 | conflict |6|Yes|
| Apr2–Jun30 2025, follow-up | simultaneously |8|Yes|
| Jul1–Sep19 2026, follow-up | overwrite |8|Yes|
| Apr2–Apr30 2025, follow-up | conflict |0|No|
| Apr2–May15 2025, follow-up | editing |8|Yes|

The Apr–Jun2026 `overwrite` query nominated May13. Follow-up chat context established the shared artifact and actors. Commit-ID searches then tried to find operations, but newer repeated references crowded the eight-result windows; narrow actor timelines were much more effective. The complete, short tool windows exposed the actual deletion and repair commands. Individual raw fetches separated commands/results from narration and verified provenance. No candidate from the early/late sampled windows was promoted on conversational language alone.

These are **48 returned chat search rows**, possibly overlapping, not48 independent episodes or opportunities. Queries varied by stratum and capped matches generally select newer records. This is deliberate temporal breadth, not representative stratified sampling. A zero result means no indexed-excerpt hit for that query/window, not no relevant behavior. A complete corpus index does not make a capped query exhaustive. No claim is made that this case was found by an already automated natural-language discovery feature.

## Reconstructed API recipe for this case

This is a reproducibility recipe **after discovery**, not a blind-finding benchmark:

1. `search(q="overwrite", table="chat_messages", from_time="2026-04-01T00:00:00Z", to_time="2026-06-30T23:59:59Z", limit=6)`: nomination.
2. `context(seed="chat_messages:7dfa22fc-d139-4318-8f6f-8b7d1977d2ce", before=15, after=20)`: commitments, peer diagnosis, acknowledgement. Context is bounded/truncated; do not present it as full conversation.
3. `timeline(agent_id=<actor>, table="computer_use_turns", from_time=<start>, to_time=<end>, limit=<cap>)` for each actor: Gemini17:48–17:58:30 cap60, Claude17:54–17:58:30 cap40, GPT17:58–18:05 cap50. These responses were complete within their requested scope.
4. `record(table="computer_use_turns", source_id=<anchor>, raw=True)`: inspect `agent_action`, `output`, `error`, timestamp and session. Fetch chat anchors similarly. Locally verify SHA256 on full original bytes before selecting fields.
5. Join actors through exact repository+branch+path+commit identities. Show before/action/after, local-vs-published status and alternative explanations. A shared word, session adjacency or named agent mention is not this join.

`probe.py` reproduces bounded calls and logs limits. `verify_sources.py` fetches only the selected anchors, checks complete hashes and writes selected fields to `evidence.json`; delete that derivative to refetch all anchors. It never executes a historical command. Authentication stays in the existing local token file and is not in the packet.

## Acceptance benchmark for the generic review backend

Run the minimal prompt above with no IDs in its input, then separately evaluate a scoped prompt restricted to May13. The unscoped prompt is a **discovery** test; the May13 prompt is an **investigation** test. Do not claim success at discovery merely because the scoped test reconstructs this known episode.

For a case it does nominate, require these auditable outputs:

- Stated eligible situation: changing a shared artifact under an own-row correction request.
- Commit/ artifact evidence connects at least two agents; no graph-edge inference from co-occurrence alone.
- Action evidence includes the whole-line filter and its mismatch with a judge-field ownership boundary.
- Outcome separates local re-ingestion, rejected publication and eventual successful publication.
- Counts distinguish damaged300/99, partial330/110, restored360/120 and planned480/160. An answer asserting “complete dataset” without the denominator distinction fails.
- Counterevidence includes legitimate original correction, immediate acknowledgement, continued methodological uncertainty and the21-vs20 recognition discrepancy.
- Acknowledgement is not called durable correction uptake; missing judge rows are not labeled free riding.
- Query scope, time windows, capped queries, raw truncation and unresolved questions are visible. Source hashes are provenance checks, not endorsements.
- Historical commands remain untrusted source data. Stderr containing a successful push is not auto-classified as failed execution.

Useful outcome criteria for discovery are number of nominated cases with verified artifact links and investigator time to reject unsupported candidates. Do not report model-behavior prevalence from these purposive searches.

## UI gaps encountered in the actual investigation

1. **Narration hides the decisive tool result.** A 2,000-character composite excerpt may include substantial internal narration before the action result. A compact “Action / stdout / stderr” view would make the distinction inspectable and avoid promoting narrative claims into verified outcomes. Label stderr accurately; it is not synonymous with failure.
2. **A cross-agent artifact is the traversal unit.** The relevant deletion and publish were in different Gemini sessions. Actor/session-only navigation fragments the episode. Offer “follow this artifact” from a cited repository/path/commit, showing exact matches and source records, without inventing a causal edge.
3. **Chat diagnosis is a lead, not a completed report.** The minimal prompt should cause follow-up raw/timeline retrieval before a finding is saved. Here both the approximate recognition count and the proposed root cause required checking.
4. **Three forms of completion differ.** Keep visible: query completeness, restoration of the already-reporting judges, and full planned experiment coverage. One generic “complete” badge would mislead.
5. **The report needs citation-level contradiction handling.** Pin the chat’s approximate loss estimate alongside the99→110→120 tool outputs and mark the extra row unresolved. Do not force the analyst into a single unsupported scalar verdict.
6. **Availability needs an explicit state.** Acknowledged correction with no later eligible opportunity is “persistence unobserved,” not0/5. Missing Kimi rows establish missing coverage, not lack of contribution.

The smallest useful interface change is a natural-language “Investigate behavior” entry that opens a review run with visible retrieval steps and then a draft incident worksheet: claims, action/output evidence, counterevidence, coverage, remaining tests. Its sources should open at the cited record in the existing workspace. This makes discovery inspectable without adding an analytics dashboard or a model ranking.

# Discovery audit

This is purposive incident discovery in the pinned AI Village corpus, not an exhaustive incident census. The deployed Observatory API was the retrieval interface throughout. No bulk source file was downloaded to the local computer, and no source data, backend, or runtime was changed.

Snapshot: `838b4150303ca8228e8edb432d8b8ccae353d258`. API coverage reports all 13 structured tables complete, totaling 3,646,304 records. An ascending timeline query and an unfiltered newest-first search bounded the corpus timestamps at **2025-04-02T17:45:08.318000Z** and **2026-09-19T00:03:19.890476Z**. These are record timestamps, not an assertion about continuous experiment operation.

## Sampling and review

The uniform discovery probe was `blocked`, restricted to `chat_messages`, taking the newest four matches in each of six contiguous calendar-quarter windows spanning the observed timestamp range. All six pages were clipped, and their cursors were not exhausted. Additional purposive probes used `handoff`, `wrong`, `fixed`, and `overwrite` across earlier quarters, followed by actor/date/term-specific searches and bounded source context. This gives temporal coverage across the pinned corpus, not complete coverage of its records, behaviors, agents, or concepts. Newest-first selection persists within each time stratum.

| Quarter | Inclusive starting bound | Inclusive ending bound | Returned / limit | Page clipped |
|---|---|---|---|---|
| 2025 Q2 | 2025-04-02T17:45:08.318Z | 2025-06-30T23:59:59.999999Z | 4 / 4 | yes |
| 2025 Q3 | 2025-07-01T00:00:00Z | 2025-09-30T23:59:59.999999Z | 4 / 4 | yes |
| 2025 Q4 | 2025-10-01T00:00:00Z | 2025-12-31T23:59:59.999999Z | 4 / 4 | yes |
| 2026 Q1 | 2026-01-01T00:00:00Z | 2026-03-31T23:59:59.999999Z | 4 / 4 | yes |
| 2026 Q2 | 2026-04-01T00:00:00Z | 2026-06-30T23:59:59.999999Z | 4 / 4 | yes |
| 2026 Q3 | 2026-07-01T00:00:00Z | 2026-09-19T00:03:19.890476Z | 4 / 4 | yes |

The audit contains **50 logged discovery calls**, of which **49 are retained**: 35 searches, 12 contexts, one timeline and one overview request. One erroneous query used an unverified agent identifier; its zero-result page was explicitly discarded and replaced after reading the agents table. It supports no absence claim. Individual raw-row verification calls are separate from these discovery-call totals.

The retained bounded responses contain **463 record appearances, 441 unique records**, including 46 agent and 51 goal metadata records; the remaining **344 unique records are behavior/session records**. These numbers describe retrieval, not exhaustive manual reading of entire rows. Search output screening used bounded excerpts, sometimes shorter than the stored 2,000-character excerpt. There were **16 appearances with clipped excerpts** and **39 responses with an envelope truncation flag**. The latter includes context boundaries and the overview's bounded action/mention aggregates; it is not a uniform measure of missing records.

The two final episodes contain **24 essential anchors** individually reviewed against raw JSON: all 24 exact quotes matched the specified source field and all 24 original-row hashes verified. Eleven supplementary raw inspections overlap those anchors; the union is **30 unique raw-verified source rows**. These checks distinguish the action sent, actual output/error, and agent interpretation. A source hash verifies bytes, not the truth of the actor's claim.

`query-log.jsonl` preserves every exact query, time bound, limit, returned count, clipping flag, next cursor and snapshot. `discovery-scope.json` contains calculated counts and definitions. `packets/` retains bounded API evidence envelopes. The final report JSON files preserve canonical source IDs, exact line/byte pointers, object generation and row hashes. They contain no raw corpus archive.

## Selection and outcome boundaries

- March 31, 2026: selected because the handoff has an explicit transferable commit, recipient actions, PR receipts, a third-party command check, a second concrete repair and a bounded workflow-success endpoint. It supports observed contribution and coordination without asserting a general cooperation effect.
- September 29–30, 2025: selected because the early loss diagnosis is explicitly revised by the designated editor and a later restoration claim complicates the outcome. It is a strong contested-observation episode, not proof of deletion or durable recovery.
- May 28, 2025: retained as a qualified candidate. A slide-edit handoff has input actions; a peer's session-ended statement is followed by successful message actions in the same session. The session schema provides no end timestamp, and visual outcome is not independently established.
- June 30, 2026: retained as a qualified candidate. Requested repository corrections were checked against raw files, but a later agent claim says the changes were committed. No after-commit check was completed, so persistent non-uptake is not established. The client scenario is synthetic.

The December 26 repair context and other screened requests were not promoted merely because agents announced fixes. Fiction, role-play and news commentary were excluded from claims of executed cooperation unless tied to identifiable tool actions and bounded outcomes. Selected incidents and repeated actors are not independent experimental replicates.

## Platform limitations encountered

1. Newest-first keyword pages overrepresent recent activity. Stratification reduces this bias but does not produce a random sample.
2. Search covers selected fields only within the first 2,000 indexed characters. A command or narrative may consume the prefix while the actual result lies beyond it. Missing search results cannot establish absence.
3. A “recorded” turn can contain agent narration or reasoning as well as actual tool fields. The report must identify whether the quote comes from `agent_action`, `output`, `error`, or chat content.
4. Default context is session- or room-scoped and clips boundaries. Actor/time searches were required to follow activity across sessions; chat rooms can be dominated by unrelated or repeated messages.
5. The current API does not expose a dedicated action-type or human/agent-speaker filter. Broad turn results include chat-send actions duplicating message records; duplicate representations are not independent corroboration.
6. Bounded source inspection did not provide document revision diffs or independently inspected screenshots. GUI coordinate clicks and actor descriptions cannot establish stable document identity or restored content.
7. An unverified agent filter returned a valid empty page rather than rejecting the identifier. Authoritative actor lookup is necessary before interpreting filtered absence.
8. The inspected May 28 session record lacks a session-end timestamp. A claim to have ended a session must not be equated with an independently established lifecycle transition.
9. Creative fiction and synthetic clients appear in the corpus. Their real recorded publication/editing actions may be analyzed, but their narrative events are not real external outcomes.
10. Overview envelope truncation applies to capped aggregates; it does not by itself mean its daily activity list is incomplete. Coverage and clipping need field-specific interpretation.

No prevalence estimates, stable personality claims, causal intervention effects, or unobserved omissions are inferred from these searches.

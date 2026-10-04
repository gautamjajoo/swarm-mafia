# Incident-report workflow review

4 October 2026. Independent read-only review of the current product UI, persistence schema, first-investigation guide, investigator contract, and validation record. This document proposes an interface and report contract; it contains no newly discovered historical episodes or measured agent effects. Root and the data/investigator agents are discovering actual episodes separately.

## Recommendation

Add one **Reports** view containing a small number of evidence-backed, analyst-curated episode dossiers. Each dossier answers a concrete question, reconstructs a bounded sequence, evaluates explicit behavioral opportunities, and opens its evidence in the existing workspace. Use “episode” until the evidence establishes an incident or failure. Keep a report readable even when its verdict is unresolved.

This is the smallest change that converts the current exploration tools into a useful research deliverable. Do not add model rankings, aggregate behavior scores, a new analytics dashboard, or another graph solely to fill the report screen. The existing relationship graph is a supporting inspection tool, not the report's conclusion.

## What the current platform already supports

| Analyst task | Available support | Remaining report gap |
|---|---|---|
| Find candidates | Excerpt search, exact-repetition candidates, participation candidates, filters | Candidate selection is exploratory; it does not establish incident prevalence or a representative case sample. |
| Reconstruct an episode | Same-room/session context, actor context across tables, recorded relationships, original JSON inspection | Bounded context windows need to be stitched into an explicitly selected episode; adjacency is not proof of a response. |
| Inspect evidence | Source IDs, matched quotes, snapshot/provenance, clipping labels, raw-record hash checks | A dossier needs a stable curated evidence manifest, with exact spans/quotes and counterevidence, independent of an AI turn's retrieval sample. |
| Challenge an interpretation | Human notes, claim-linked challenges, corrections in follow-up requests | Notes are not yet a structured claim ledger with support, contradiction, unknowns, and a reviewed disposition. |
| Preserve work | Saved investigation state, optimistic revisions, JSON export, source-view restoration | Current saved state has no report narrative, timeline, rubric application, or report version. |
| Analyze with AI | Bounded investigator, focused evidence, context, quote checking, declared limitations | At most two explicit focused source IDs enter a request. Opening a large report must not imply that every cited source was inspected by the next AI call. |
| Propose follow-up work | Unrun studies with control, metric, and guardrail | Link each proposal to a specific unresolved claim; historical report completion is not intervention execution. |

The current system is sufficient for manual discovery and source review. It is insufficient as a self-contained incident-reporting product until findings can be curated into a structured dossier. The first version can use checked-in, validated report JSON written after real evidence discovery; an elaborate report editor or new agent pipeline is unnecessary for this iteration.

## Smallest useful interface

### Report list

Add **Reports** beside Investigations. Show a short list of real curated cases: descriptive title, behavioral question, source, observed date range or unknown-time label, involved recorded actors, review status, and one sentence describing the limited finding. Show “Evidence insufficient” honestly when that is the outcome. Do not use a severity score unless a separate impact definition and observed impact evidence exist.

Make the selection statement visible above the list: “Purposively selected episodes for close analysis; these reports do not estimate corpus-wide prevalence.” Include the discovery rule for each case, such as a particular search and subsequent context expansion. Do not equate the number of reports with number of incidents found across the corpus.

### Report detail

Use one scrolling document with five compact sections and a persistent **Open investigation workspace** action:

1. **Question and finding.** Title, source snapshot, analyst/review status, report version, bounded scope, and a two- to four-sentence conclusion. Clearly label what is observed, inferred, and unresolved. Put scope limitations beside the conclusion rather than only at the bottom.
2. **What happened.** A curated timeline of roughly 5–12 meaningful records, enough to expose the trigger, relevant instruction, interaction, action, and strongest available outcome. Each row has recorded actor, event time or source-order position, exact source ID, a short description, and **Inspect evidence**. Include intervening counterevidence and recovery; do not omit inconvenient events to make a cleaner story.
3. **Claims and competing evidence.** Short claim cards with separate supporting evidence, counterevidence, and missing evidence. Use states `supported_within_scope`, `contradicted`, `mixed`, or `insufficient_evidence`; each remains separate from human review status. “No counterevidence found in this search” must include the inspected scope and cannot become “No counterevidence exists.”
4. **Behavioral rubric.** A small table evaluating only the opportunities that the episode actually contains. See the contract below. One click opens the instruction/action or handoff pair that justifies each assessment.
5. **Limits and next check.** Missing logs/artifacts, source gaps, clipping, alternative explanations, and one or two precise retrieval or proposed-study steps. Distinguish “available in this corpus” from “external evidence required.”

On desktop, selecting a quote or timeline row may open the existing source inspector adjacent to the document. On mobile, use the existing single-surface inspector and preserve a return-to-report action. It is more valuable to inspect a specific claim quickly than to show an entire network at once.

## Report-to-workspace contract

The document view should work from frozen report evidence, while opening the workspace performs fresh retrieval explicitly.

- **Inspect evidence:** Open the exact source record with the report's quoted passage available. If the current excerpt differs or no longer contains it, retain the captured report quote and say that current retrieval differs. An inaccessible record does not erase the original report evidence.
- **Open timeline row:** Set the selected ID and independent context seed, source, and actor/source mode. Use the report's episode bounds where compatible with the context API; otherwise state that the context expansion crosses report bounds.
- **Open claim:** Load its support and counterevidence pins and a specific question. Prioritize at most two explicit focused IDs for the current investigator; show the exact selected IDs and distinguish other report pins that remain available for manual inspection. Do not promise that all report citations enter one model call.
- **Open full report:** Create an unsaved workspace initialized from the case's source, report ID/version, scope, evidence pins, analyst notes, and question. Honor the existing unsaved-work guard. The analyst must choose Save to persist a personal working investigation. Opening a curated case must not overwrite its published interpretation.
- **Return to report:** Preserve the case/version and scroll position. A report-linked workspace can be exploratory without silently changing the curated report.
- **Export report:** Include readable report content plus JSON evidence references, snapshot/provenance, selection rule, reviewed claim/rubric values, and limitations. Source text and model suggestions remain explicitly untrusted data. Initial JSON download is sufficient; Markdown export is optional if it preserves those boundaries.

The curated report is an analyst-authored artifact. Its existence does not mean all evidence has been independently verified, nor that an AI-generated claim has become true. Display the actual review process and any remaining disputes.

## Behavioral rubric: no unavailable-to-zero conversion

Use categorical assessments first. The initial report view needs no composite number. For every row preserve three distinct dimensions:

| Dimension | Allowed states | Meaning |
|---|---|---|
| Opportunity/applicability | `present`, `absent`, `uncertain` | Was there a specific correction, applicable preference, handoff, conflict, or failure to evaluate? |
| Observability | `sufficient`, `partial`, `unavailable` | Are the relevant instruction, action, and follow-up records actually present and attributable? |
| Assessment | `consistent`, `inconsistent`, `mixed`, `not_assessable` | What does the observed behavior establish within that opportunity? |

An absent opportunity yields **Not applicable**, not a favorable score. An uncertain opportunity or unavailable behavior yields **Not assessable**, not a failure or zero. Partial observation can support a narrow statement but must not support an unobserved outcome. Explicit counterevidence remains visible even if the final assessment is mixed or disputed.

| Rubric dimension | Minimum evidence needed | Useful episode-level question | Invalid shortcut |
|---|---|---|---|
| Correction uptake | Applicable correction, target, relevant subsequent action, ordering, and any superseding instruction | Did the next observable relevant action follow the correction? | Treating acknowledgment as compliance, or lack of a later record as noncompliance. |
| Preference preservation | Explicit user preference with scope, handoff/context where relevant, later applicable action | Was the stated preference preserved across the observed steps? | Calling an analyst preference a user instruction; assuming it applies forever. |
| Delegation boundaries | Delegated task, explicit authority/constraints, recipient identity/context, observed action | Did the child action conflict with an explicit boundary visible in the record? | Calling an action unauthorized because the relevant parent context was not captured. |
| Negotiation | Recorded competing proposals or conflict, responses, decision/revision where observable | Was disagreement clarified, resolved, escalated, or left unresolved? | Equating message count, politeness, or consensus language with good negotiation. |
| Recovery | Recorded failure/conflict, changed action or strategy, subsequent result evidence | What was attempted after the failure, and what supports the claimed outcome? | Treating a retry, later success claim, or different later outcome as proof of recovery or causality. |

For recovery, display outcome basis separately: `agent_claim`, `tool_report`, `artifact_evidence`, or `unverified`. For actor attribution, distinguish the message's recorded speaker from an agent/session association; a tool or user message inside a session is not automatically authored by that session's agent.

If numerical scoring is added later, keep `null` with an explicit unavailability reason, publish the item anchors and applicable/observable denominator, and retain individual assessments. Never impute missing rows as zero, average inapplicable opportunities, compare models across unmatched task populations, or call a convenience-sample difference an improvement.

## Selection and denominators

Every dossier needs a compact method statement:

- Why this episode was selected: discovery query/rule, snapshot, filters, and any manual inclusion decision.
- Episode boundary: start/end records and why they bound the question; distinguish a time range from a session or causal episode.
- What was inspected: tables, record IDs, context expansions, raw records, and any unavailable channels/artifacts. Complete table ingestion does not mean every raw field or image was inspected.
- Duplicate representation policy: an event and its linked chat record may describe one action. Count behavioral opportunities/unique incidents only after resolving that relationship; do not use raw row count as action count.
- What a count means: separate retrieved rows, eligible opportunities, assessable opportunities, reports, and unique incidents. A report set selected for failures cannot estimate failure prevalence or compare agent/model quality.
- Counterevidence search: record where and how it was sought; absence of a match in excerpt search does not establish absence from the corpus.

If a case says “two corrections were followed,” expose the two opportunity IDs and how their outcomes were determined. If one additional correction has no observable follow-up, report “2 consistent of 2 assessable; 1 additional opportunity not assessable,” without implying a population success rate.

## Minimal report data contract

Use a small validated schema rather than prose embedded directly into JSX. Required fields:

```text
report:
  id, version, title, question, source, source_snapshot
  review_status, author_or_curator, reviewed_at
  selection_method, episode_scope, inspected_scope, limitations
  conclusion: observed, interpretations, unresolved
  evidence[]:
    evidence_id, canonical_record_id, source_snapshot, provenance/hash_basis
    quote_or_span, quote_scope, excerpt_truncated, actor_attribution_basis
  timeline[]:
    entry_id, evidence_ids, description, timestamp_or_order, ordering_basis
  claims[]:
    claim_id, text, evidence_status, review_status
    support_evidence_ids, counterevidence_ids, missing_evidence, alternatives
  rubric[]:
    dimension, opportunity_id, applicability, observability, assessment
    reason, evidence_ids, counterevidence_ids, outcome_basis
  proposed_next_checks[]:
    question, available_corpus_or_external, linked_claim_ids
  workspace:
    source, filters, selected_id, context_seed, context_mode, focus_ids
```

Validate that all referenced evidence IDs exist, every assessment has evidence or a stated inability to assess, and no executed-study or causal-effect status is invented. A source capture timestamp differs from the historical event timestamp. Preserve null values; never fill them with epoch-zero or ingestion order disguised as event time.

For the first release, report creation can remain outside the UI: checked-in case JSON plus a validated report-detail component and the workspace-opening adapter. Keep edits to the report data reviewable. Promote to a database/editor only when report authorship workflow requires it.

## Minimal acceptance checks

1. Each reported episode has actual fetched source records, a declared selection rule, and a bounded timeline. No fixture is presented as observed historical behavior.
2. Every material factual claim opens supporting evidence; counterevidence is reachable with equal prominence. The report remains readable when one live source fetch fails.
3. A case with no recorded user preference displays **Not applicable** or **Opportunity uncertain**. A case with a preference but missing follow-up displays **Not assessable**. Neither appears as zero or successful behavior.
4. Opening a claim passes only its declared current focus to AI and retains all other evidence for manual inspection. The UI does not imply the entire dossier was automatically analyzed.
5. The report's context center and selected record survive workspace save/reopen independently. Returning to Reports leaves the curated report unchanged.
6. An event/chat duplicate counts once when discussing actions; displayed denominators are reconstructible from the case's opportunity list.
7. Reports visibly separate historical observation, analyst interpretation, missing evidence, and proposed future study. No unrun study has an effect estimate.

## Delivery order

First finish one real episode with sufficient context and counterevidence, even if only one or two rubric dimensions are assessable. Build the report detail around that actual material, then add one contrasting episode if the source supports it. Add the Reports list and workspace links last. A single defensible report is more useful than multiple thin narratives presented as completed investigations.

Retain the accepted scope decision to defer the aggregate name-mentions graph until its edges open exact matching messages. It is not required for the report workflow.

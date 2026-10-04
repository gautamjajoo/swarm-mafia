# Kairosity investigation workspace

Design specification · 4 October 2026 · Proposed product behavior, not measured product performance

## Product job

Help an agent developer or researcher answer a specific behavioral question, inspect the relevant historical evidence, preserve disagreements, and turn a defensible finding into a proposed evaluation. Codex, Claude, and Cursor are target consumers of portable investigation packets; product integration is not assumed to exist.

The initial sources are AI Village and SwarmTraces. Their historical records can support observations, candidate explanations, and proposed studies. They do not demonstrate that Kairosity improves an agent, that a suggested intervention works, or that one agent/model is generally better. Keep this limitation in the finding model and language rather than relying on a footer disclaimer.

Local research context: [evaluation memo](../research/evaluation-research.md). The current SwarmTraces sample manifest records partial archive coverage, and its metadata has null minimum/maximum timestamps. The interface must represent partial coverage and unknown time explicitly; source IDs or ingestion order must never silently become execution order.

## Default screen and information architecture

Open directly into an investigation, with the latest saved investigations accessible from a narrow navigation rail. Avoid a marketing homepage, decorative metrics, or a full-corpus force graph as the first screen.

| Region | Content and primary interaction |
|---|---|
| Navigation | Investigations, Sources, Findings, Proposed studies. Each item is a working surface. |
| Header | Editable investigation title; visible scope chips; save state; Share/export. Scope includes source snapshot, episode/session, agents, event types, and available temporal bounds. |
| Question bar | A concrete question with an Analyze button. Suggested questions are optional starters. The submitted question remains visible throughout the investigation. |
| Central canvas | A bounded evidence graph with a Timeline/Graph split toggle. Default to a selected episode or search neighborhood; show loaded/total counts and truncation. |
| Timeline under canvas | Agent lanes, source order or recorded timestamps, event markers, selected range. Unknown-time records remain in an explicitly labeled source-order lane. |
| Right inspector | Selected event/edge/finding. Exact source text, surrounding records, provenance, annotations, and Pin evidence. This is resizable and can be expanded for long records. |
| Bottom/side notebook | Persistent pinned evidence, analyst notes, AI analysis, and draft findings. Tabs or a drawer prevent squeezing four unreadable panels onto a laptop. |

At approximately 1440px, use a 64px navigation rail, flexible canvas, and 380–440px inspector. At narrow widths, use a single active surface with persistent selection and a clear back action. The timeline remains keyboard accessible even when the graph is hidden.

## Natural investigation flow

1. **Choose a scope.** Start from a source, episode, event deep link, saved finding, or search result. Show what is indexed, absent, redacted, or inferred before running analysis.
2. **Ask a question.** Example: “After the user corrected the target, did downstream agents use the corrected target?” The question and scope form a versioned analysis request.
3. **Review candidate evidence.** Return cited observations first, candidate explanations second, and explicit unanswered questions. Expand a citation to its exact span and neighbors. An AI result with no evidence is an ungrounded suggestion, not a finding.
4. **Inspect and pin.** Select events in either view; follow typed relationships; pin exact passages as support, counterevidence, or context. Source expansion is explicit so the original scope is not silently changed.
5. **Annotate and dispute.** Write a note on a span, dispute a relationship, or edit a claim. Keep original AI text and human revisions separately with authors and timestamps.
6. **Save a finding.** Save a specific claim, supporting and contradicting evidence, coverage limits, and reviewer disposition. A finding may remain “Insufficient evidence.” Saving does not imply confirmation.
7. **Compare or propose a study.** Search for similar episodes using visible criteria or create a proposed evaluation that specifies what data and intervention are required. Historical inspection ends here unless a separately instrumented execution system exists.

## Graph and timeline contract

- The selected object ID, scope, focused neighborhood, and timeline range are shared state. Clicking a graph event scrolls and highlights its timeline row; clicking a row centers the graph on that event and opens the same inspector. Provide a recenter button rather than animated camera jumps on every hover.
- Hover previews; click selects; a separate Expand action fetches one-hop neighbors. Preserve graph positions while inspecting. Indicate hidden neighbors and offer bounded expansion with counts.
- Represent agents, events, artifacts, instructions/constraints, and findings as distinguishable node types. Node label and icon accompany color. Collapsed event groups show their count and aggregation rule.
- Solid edges encode source-supported relations such as `sent to`, `reply to`, `used`, `produced`, or an explicit parent relation. Dashed edges encode derived or analyst-proposed relations. A legend is always one click away, with no ambiguous “influences” edge.
- Selecting an edge reveals its type, originating record/span or derivation, author, and review status. A chronological edge is labeled order, not cause. Agent attribution is unknown when the source does not support it.
- Timeline zoom/range filtering changes the visible subgraph and states how many nodes are hidden. “Keep pinned evidence visible” may show out-of-range pins with an explicit badge, never quietly include them in counts.
- Search highlights matching spans and offers source-neighborhood expansion. Normalized text and original payload remain separately inspectable. Links open the exact source locator where available.
- Missing timestamps, redacted content, unresolved artifact versions, disconnected fragments, and duplicate/recovered records are first-class visual states. Derived/recovered text retains a link to its origin and is not automatically counted as an independent event.

## Evidence inspector and human review

Every evidence view includes source name, snapshot/version, immutable record ID, locator, available event time, ingestion time, agent attribution status, and exact quoted span. Show raw payload as inert text. Keep surrounding context accessible without replacing the selected quote.

Pinning creates a stable reference containing record ID, span offsets or locator, source snapshot, and content hash. If a source revision invalidates a span, mark the pin stale and preserve the old version. Notes are independent objects, not mutations to source text.

Annotations have four simple kinds: Note, Supports, Contradicts, and Needs context. A dispute records a reason and optional alternative interpretation; it can target a span, edge, or claim. Reviewers can agree, disagree, or mark unresolved. Two reviewers disagreeing remains visible until explicitly adjudicated; no majority vote silently overwrites evidence.

Use two separate finding dimensions:

- **Evidence status:** Supported by inspected records / Contradicted / Insufficient evidence.
- **Review status:** AI draft / Human reviewed / Disputed / Archived.

“Supported” is scoped to the claim and inspected records. A source-reported success remains distinct from an independently verified outcome. The inspector must expose the exact basis of any outcome label.

## AI collaboration

The AI panel operates on the current scope and explicitly selected pins. Before running, show the selected sources, scope size, and intended operation. During a run, show useful progress such as “Searching correction references” and allow cancellation. Persist run IDs and errors.

Useful follow-ups are evidence operations: “Find the later action,” “Look for counterevidence,” “Trace this handoff,” “Explain this relationship,” “Compare another episode,” and “Draft a study from this finding.” Generated follow-ups are proposed actions, not automatically executed searches or scope changes.

Each response has a compact structured shape: observations with citations; candidate explanation; counterevidence; missing evidence; next checks. Citation activation synchronizes the inspector, graph, and timeline. The analyst can pin any observation or convert it to a draft finding. Never collapse “the agent said it would comply” into “the agent complied.”

Record model identifier, prompt/rubric version, retrieval query, inspected record IDs, source snapshots, scope expansion, and run budget with every AI result. Confidence numbers are omitted unless there is a defined, evaluated calibration method. Trace contents cannot modify analysis instructions or execute commands.

## Comparing scopes

Compare two frozen scopes side by side using the same question and rubric. Show their episode counts, qualifying opportunities, missingness, task/source composition, and available instrumentation. The user can edit inclusion criteria and see affected counts.

Start with paired case comparison: aligned instruction → handoff → action → observed outcome, with evidence citations in every cell. A “missing” cell is different from a negative result. Do not align events by absolute time when timestamps are unavailable; align by behavioral stage with the mapping visible.

Aggregate rates require a reviewable denominator: for example, “3 of 7 reviewed correction opportunities; 4 additional candidates unreviewed.” Expose the underlying case list. Do not compare raw agent counts across incompatible corpora or infer model quality from a convenience sample. Label discovered patterns descriptive and exploratory.

## Three useful workflows and their verifiable outputs

### 1. Correction uptake and preference preservation

**Question:** After an explicit correction or stated preference, what later action is consistent or inconsistent with it?

**Flow:** Find the instruction/correction; identify its target and applicability; inspect any acknowledgment; follow handoffs and artifact references; inspect the first and subsequent relevant actions; search for counterevidence or later superseding instructions. The analyst marks ambiguous applicability rather than assuming every later action must follow every earlier statement.

**Output:** A correction ledger with instruction span, effective scope, acknowledgment span, relevant action span, conflicting or superseding instruction, and one of `consistent`, `inconsistent`, or `unobservable`. A finding states exactly which action conflicts with which applicable instruction. Every nonempty field links to a source span.

**Verification:** Opening any ledger row reproduces the cited instruction and action. Acknowledgment without observable action yields `unobservable`. Unknown ordering is disclosed and prevents a firm uptake claim.

**Proposed study:** Compare an explicit correction/constraint handoff mechanism with a baseline on held-out tasks, measuring action-level adherence and task completion. Preserve current user preferences as explicit, versioned constraints. Historical evidence supplies candidate cases, not an estimated treatment effect.

### 2. Delegation boundary and information transfer

**Question:** Which delegated actions were authorized, and which relevant constraints are visible in the receiving agent's context?

**Flow:** Select a parent request or handoff; inspect its explicit boundaries; trace recipient messages, relevant context/artifact references, and actions; distinguish absent-in-record from absent-in-context; compare the parent's stated intent with the child action and available result evidence.

**Output:** A handoff matrix containing delegator, recipient, requested task, explicit authority/constraints, visible transmitted evidence, child action, and observed result. Findings distinguish `explicit boundary conflict`, `possible context omission`, and `insufficient record`.

**Verification:** Every edge has source provenance. The UI cannot label a child as unauthorized solely because the parent's context was not captured. The matrix exposes missing context and inferred identity mappings.

**Proposed study:** Test a structured delegation contract containing constraints, allowed actions, escalation conditions, and completion evidence. Evaluate boundary adherence and useful task completion separately; do not reward blanket refusal as successful delegation.

### 3. Negotiation and recovery after disagreement or failure

**Question:** Following a conflict, correction, or failed attempt, what changed, and what evidence supports recovery?

**Flow:** Select the trigger; inspect competing proposals and relevant constraints; follow subsequent decisions, retries, and artifact versions; distinguish repeated attempts from a material strategy change; locate the strongest available outcome evidence and any unresolved contradiction.

**Output:** An episode strip: trigger → alternatives → decision → attempted change → observed outcome. Include a recovery table with `claimed`, `tool-reported`, `artifact-supported`, or `unverified` result basis, plus contrary evidence. A success claim cannot erase a preceding or unresolved error.

**Verification:** Each stage opens its evidence. Missing outcome evidence remains unverified. A different later outcome is described as following the change, not caused by it.

**Proposed study:** Compare explicit conflict resolution and escalation protocols on controlled task variants with repeated stochastic runs. Record quality, adherence, number of attempts, and resource cost. Claim improvement only after a separately executed evaluation with a declared design and results.

## Saved objects and backend contract

Use stable identifiers across the private Sites frontend and GCE SQLite evidence API. Frontend state must not invent facts absent from the backend.

| Object | Minimum persistent content |
|---|---|
| Investigation | ID, title/question, owner, versioned scope, source snapshots, saved view state, created/updated time |
| Evidence pin | Record ID, source version/hash, exact span/locator, role, author, note |
| Annotation/dispute | Target ID/span, type, text, author, timestamp, revision history, resolution |
| Finding | Claim, evidence status, review status, supporting/counterevidence pins, unknowns, scope, rubric, authorship/revision history |
| Analysis run | Input scope and pins, model/prompt versions, retrieval log, inspected IDs, structured output, completion/error state |
| Proposed study | Linked finding, research question, intervention and baseline, task population, outcomes, data/instrumentation needed, execution status `proposed` |

Suggested capabilities: source manifests; bounded search; event details and neighbors; typed subgraph queries; paginated timeline; investigation/pin/annotation/finding persistence; analysis runs; compare scopes; packet export. Expose query coverage and truncation in responses. Use cursor pagination and stable order, with an explicit unknown-time strategy.

A portable investigation packet contains Markdown findings, JSON evidence references and scope definitions, provenance/manifests, and proposed evaluation cases. This enables human researchers and coding agents to consume the same claim and evidence. An exported proposal is not an installed regression test, live IDE integration, or executed study.

## Delivery priorities

**First usable product:** real scoped sources and coverage; synchronized graph/timeline/source inspector; exact citations and pinned evidence; persistence; human notes/disputes; cited AI follow-ups with clear failure states; saved findings; portable export. Implement one correction/handoff investigation end to end before expanding taxonomy.

**Next:** paired scope comparison, review queues, source snapshot updates and stale-evidence handling, structured study drafting, API access for coding-agent clients, reviewer roles and audit history.

**Requires separate validation and instrumentation:** intervention replay, automated regression execution, calibrated scoring, live integrations, or claims of agent improvement. No disabled button should imply that these already work.

## Independent acceptance checklist

- A first-time analyst can state the current question, source scope, coverage, and selection without opening settings.
- Selecting the same event in search, graph, timeline, or a citation opens the same record and preserves its immutable ID.
- A pin survives reload and source refresh; stale source versions are visible.
- Every displayed count is recomputable from visible criteria and backend records. Zero, unknown, not loaded, and not applicable are different states.
- Graph truncation and timeline filtering disclose hidden evidence; partial loading never appears to be a complete trace.
- At least one contradictory and one insufficient-evidence finding can be saved and exported without UI pressure to resolve them.
- Human edits retain original AI output, authorship, and the change history. Disputes survive reload.
- AI failures, cancellation, unavailable source context, and API errors leave the notebook intact and give a useful next action.
- Keyboard users can reach source inspection, pinning, annotations, findings, and exports without interacting with graph geometry.
- Exported packets reopen exact source references, include coverage limits, and contain no claim of measured improvement unless an actual study result is linked.

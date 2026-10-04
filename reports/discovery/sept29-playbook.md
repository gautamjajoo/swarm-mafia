# Apparent document loss gives way to an “intact” correction

Several agents announce edits to a shared Playbook, then report missing content and propose a single editor. The editor later says the document is mostly intact. A next-day restoration claim leaves durable recovery unresolved.

The trace establishes overlapping edit intentions, a typed appendix, a coordination proposal and acknowledgment, and a material revision of the editor’s diagnosis. It does not establish that concurrent editing deleted the document. The next-day restore claim also prevents treating the first day’s all-clear as a verified durable repair.

Window: 2025-09-29T18:30:33.396475Z through 2025-09-30T17:26:16.011337Z. Snapshot `838b4150303ca8228e8edb432d8b8ccae353d258`. Twelve essential rows reviewed; all quotes match individually hash-verified original rows. Source-byte verification does not validate an agent’s claim.

### 1. o3 announces an appendix edit

2025-09-29T18:30:33.396475Z · o3 · `chat_messages:b35f8ed2-bd9c-4df0-9f49-89ffc06ddf06`

> Adding the cleaned six-line Hindrance/Nudge/Strength

One announced editor of the shared Playbook. Concurrent intent does not by itself prove destructive collision.

### 2. Sonnet announces another edit in the same period

2025-09-29T18:30:42.935198Z · Claude 3.7 Sonnet · `chat_messages:1a3d6700-6be6-4407-a8e7-2e8ff58e1e65`

> Rather than waiting for consensus

Sonnet says it will directly fix formatting. This is an announced plan, not verified document mutation.

### 3. An appendix heading is actually typed

2025-09-29T18:36:22.951316Z · o3 · `computer_use_turns:ec5783c9-5299-4784-b9ea-8168d835614a`

> Appendix A — H/N/S Quick Reference (29-Sep-25)

The input action is recorded. It does not establish its final location, what was selected, or that this edit deleted other content.

### 4. Opus reports missing structure

2025-09-29T18:42:36.254261Z · Claude Opus 4.1 · `chat_messages:e9e5808f-91ee-4e97-a1b2-36349d77fd4a`

> the document structure seems to have changed significantly

This is a contemporaneous observation claim, not a source-level document diff. Opus attributes the problem to simultaneous editing.

### 5. A designated repair editor volunteers

2025-09-29T18:44:42.520164Z · Claude 3.7 Sonnet · `chat_messages:6d2e8395-1357-4222-8aff-48c77a6e90aa`

> I'll volunteer to be the document editor.

Sonnet proposes serialized editing and preserving valid additions.

### 6. Another editor agrees to pause

2025-09-29T18:46:06.784503Z · o3 · `chat_messages:c0460b52-2bd2-49f2-9c02-82a77c3c8ef0`

> will refrain from further edits

o3 explicitly accepts the coordination constraint. This message alone does not prove all agents complied indefinitely.

### 7. First restoration attempt reports partial progress

2025-09-29T18:59:21.399195Z · Claude 3.7 Sonnet · `chat_messages:0f4fc1c2-2c21-485a-bf8c-e66832795e35`

> couldn't complete the full restoration

Sonnet still describes missing content and technical obstacles.

### 8. A different document access path is attempted

2025-09-29T19:02:55.678690Z · Claude 3.7 Sonnet · `computer_use_turns:492e2f7f-fe48-4701-b0e0-9b4a68f2b2ee`

> left_click

Recorded click occurs while the agent says it is opening the PDF with Google Docs. The target is its screen interpretation; raw coordinates alone do not identify the artifact. A different rendering/version is an alternative explanation.

### 9. The editor now reports substantial existing content

2025-09-29T19:06:43.480935Z · Claude 3.7 Sonnet · `chat_messages:734cbc0d-b3fe-4532-bc03-df5e4e347760`

> it appears most of the content from the PDF has already been transferred

Observation changes within minutes; this does not reveal who transferred content or whether the same underlying document was displayed.

### 10. Explicit correction: mostly intact, not empty

2025-09-29T19:15:47.583698Z · Claude 3.7 Sonnet · `chat_messages:9fc29bac-ce29-4c6f-90de-300ca935d278`

> actually mostly intact, not empty as we initially feared

Key counterevidence against treating the original near-wipeout diagnosis as established. The editor says it preserved the appendix and changed its style.

### 11. Next-day restore-confirmation click is recorded

2025-09-30T17:09:20.011152Z · Claude Opus 4.1 · `computer_use_turns:2de3323c-fb2c-436e-80e6-b1c8f4570919`

> left_click

Opus describes a Restore this version dialog and issues a click. No screenshot or document diff was independently inspected; actual restored content is not established by the click alone.

### 12. Next-day restoration is reported again

2025-09-30T17:26:16.011337Z · Claude Opus 4.1 · `chat_messages:73ca014e-3095-4a4f-9208-31ecbef05152`

> restored the Mutual-Aid Playbook from yesterday's version history

The later claim prevents interpreting the day-one all-clear as demonstrated durable recovery. It is an outcome report, not independent artifact verification.

## Claims and limits

**document-1 — observation.** Overlapping editing intentions and an appendix input action preceded reports of altered or missing structure. Intentions and a text input are not a document diff. They do not identify a destructive editor or establish actual deletion.

Support: `chat_messages:b35f8ed2-bd9c-4df0-9f49-89ffc06ddf06`, `chat_messages:1a3d6700-6be6-4407-a8e7-2e8ff58e1e65`, `computer_use_turns:ec5783c9-5299-4784-b9ea-8168d835614a`, `chat_messages:e9e5808f-91ee-4e97-a1b2-36349d77fd4a`. Counterevidence: none selected.

**document-2 — observation.** A designated-editor proposal received an explicit pause commitment from o3. The acknowledgment establishes receipt of the constraint. All subsequent edits and compliance by every agent were not exhaustively reviewed.

Support: `chat_messages:6d2e8395-1357-4222-8aff-48c77a6e90aa`, `chat_messages:c0460b52-2bd2-49f2-9c02-82a77c3c8ef0`. Counterevidence: none selected.

**document-3 — observation.** The editor’s initial partial-restoration account was superseded by a report of substantial existing content and an explicit mostly-intact correction. This is a change in the actor’s account. No independent screenshot or revision diff establishes which account accurately described which document version.

Support: `chat_messages:0f4fc1c2-2c21-485a-bf8c-e66832795e35`, `chat_messages:734cbc0d-b3fe-4532-bc03-df5e4e347760`, `chat_messages:9fc29bac-ce29-4c6f-90de-300ca935d278`. Counterevidence: `chat_messages:e9e5808f-91ee-4e97-a1b2-36349d77fd4a`.

**document-4 — interpretation.** A proven concurrent-edit wipeout followed by verified durable recovery would overstate this evidence. Alternative versions, rendering, PDF conversion, or actual repair are all compatible with the bounded records. The next-day restoration is self-reported.

Support: `computer_use_turns:492e2f7f-fe48-4701-b0e0-9b4a68f2b2ee`, `chat_messages:9fc29bac-ce29-4c6f-90de-300ca935d278`, `computer_use_turns:2de3323c-fb2c-436e-80e6-b1c8f4570919`, `chat_messages:73ca014e-3095-4a4f-9208-31ecbef05152`. Counterevidence: `chat_messages:e9e5808f-91ee-4e97-a1b2-36349d77fd4a`, `chat_messages:0f4fc1c2-2c21-485a-bf8c-e66832795e35`.

## Behavioral coding

- **C3: not_assessable** (opportunity present; observability partial). Focal actor: o3, acknowledging Sonnet’s proposed editing coordination. Responsibility transfer and receipt are explicit, but artifact identity and the complete subsequent edit sequence are not independently established. Denominator: One explicit editing handoff/serialization opportunity; no verdict on all-agent compliance.
- **C4: not_assessable** (opportunity uncertain; observability partial). The repair and pause statements lack an established agreed deadline or closure rule; the alleged final document state is self-reported. Denominator: Candidate commitments only; no eligible closed-window fulfillment denominator.
- **C5: not_assessable** (opportunity uncertain; observability partial). Agents propose repair under conflicting observations, but no independent contemporaneous document state is available to establish whether reliance on the diagnosis was calibrated. Denominator: No independently assessable recommendation-linked decision counted.
- **C6: not_assessable** (opportunity uncertain; observability partial). Sonnet explicitly revises the missing-content account, which is descriptive evidence of revision. Independent validity of either document-state claim and stable artifact identity are missing, so this is not a scored valid-correction uptake. Denominator: One candidate revision episode; independently valid correction denominator not established.

## Limitations

- No independently inspected screenshots, document diffs, revision identifiers, or stable artifact identity across the PDF/Google Docs path are included.
- A recorded click proves an input action, not the selected UI target, completion, or restored content. Target descriptions are the agent’s interpretations.
- Near-wipeout, concurrency causation, and successful restoration are claims made by agents, not independently established artifact facts.
- The day-one intact correction and day-two restore claim may concern different versions, rendering, or real changes; this packet cannot adjudicate them.
- A pause acknowledgment does not prove later compliance; absence of a retrieved edit is not negative evidence.
- No conclusion about the underlying Playbook advice, agent traits, or intervention effectiveness follows.

Exact provenance, row hashes, query parameters, and canonical claim pointers are in the companion JSON and discovery audit.

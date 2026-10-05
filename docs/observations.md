# Three investigations to try in Swarm Mafia

These walkthroughs use the selected, reviewed anchors served by the product. Open **Findings**, choose the report, then use **Follow the evidence** to open each numbered step beside its original quotation. **Inspect in workspace** brings the source into a new investigation so you can follow related records and add a challenge.

The complete public anchor collection is [product/data/report-catalog.json](../product/data/report-catalog.json). Each entry includes the exact source ID, UTC timestamp, source-field quotation, snapshot, object generation, byte/line pointer, and original-record hash check. The underlying private dataset and working caches are not distributed here. Hash matching establishes the identity of the source bytes, not the truth of what an agent says.

<a id="shared-work"></a>
## A local fix damaged shared work

Catalog report ID: `shared-work-repair`.

### Step 1: The promised fix concerns the agent’s own rows

**Gemini 3.1 Pro · 2026-05-13T17:44:02.197090Z**

The explicit scope is replacing its own synthetic rows, not all rows mentioning the same model.

Source: `chat_messages:55cfc128-0d72-4995-9948-42176fd78af1`.

### Step 2: A whole-line filter crosses the ownership boundary

**Gemini 3.1 Pro · 2026-05-13T17:52:10.616469Z**

The model name also occurs in the author column of peers’ scores. Output is null here; later matrices establish the effect.

Source: `computer_use_turns:00092faa-0755-4263-8846-2e5fb62e42e7`.

### Step 4: The shared score count falls to 300

**Claude Opus 4.7 · 2026-05-13T17:56:18.206167Z**

The analyzer reports 300 score rows and 99 recognition rows. Its planned totals include a fourth judge; compare the three reporting judges’ 360 prior score rows.

Source: `computer_use_turns:ec762292-51e7-4bcf-aa83-86f0e25764e7`.

### Step 8: A precise handoff tells the second peer what to restore

**Claude Opus 4.7 · 2026-05-13T17:58:09.806497Z**

The request names the owner, source sheets, and ingestion procedure. This is actionable assistance rather than generic encouragement.

Source: `chat_messages:7dfa22fc-d139-4318-8f6f-8b7d1977d2ce`.

### Step 10: Re-ingestion recovers 360 score rows

**GPT-5.5 · 2026-05-13T18:01:21.615385Z**

Actual ingestion output contains all 12 judge–author score cells and 120 recognition rows. This is a local result pending publication.

Source: `computer_use_turns:b12ddbd4-5ebd-4c6f-a44a-a3dea14ddc7b`.

### Step 12: The final check confirms the repaired branch and matrix

**GPT-5.5 · 2026-05-13T18:02:54.162784Z**

Recorded HEAD and origin both identify the repair commit. The matrix confirms row coverage; score-value equality and study validity are separate questions.

Source: `computer_use_turns:8db9ffa0-8838-47d6-bc44-30b35a04b28a`.

**Question to pursue:** “Which field identified the row owner, and why did filtering the whole line remove other judges’ scores?” The before/after matrix matters more than an agent saying the repair worked. Restored row coverage does not validate the scientific study or establish lasting improvement.

[Read the detailed account](../reports/deep/coordination/report.md).

<a id="pricing"></a>
## An uncertain price became a competitive signal

Catalog report ID: `competitive-price-signal`.

### Step 2: Opus labels $15.69 as supplier base price

**Claude Opus 4 · 2025-07-02T18:55:31.061400Z**

The agent’s earlier interpretation of this number is a supplier base price. It is an alternative explanation, not independent accounting verification.

Source: `computer_use_turns:8723e504-c2ff-4d32-b190-212e4355bd8f`.

### Step 4: The same number is interpreted as a customer discount

**Claude Opus 4 · 2025-07-11T18:16:38.122036Z**

The later description interprets the same number as a customer discount. The historical screenshot and transaction ledger were not independently inspected.

Source: `computer_use_turns:ae8b7b11-0a63-4633-93fa-951c6e4ec274`.

### Step 9: Explicit competitive rationale incorporates the unverified price

**Claude 3.7 Sonnet · 2025-07-14T18:14:59.488155Z**

The stated pricing rationale explicitly incorporates the unverified rival price. Gemini’s separate price and the deadline are additional inputs.

Source: `chat_messages:6aaadc6a-a716-48ad-a466-69c8fbe611b2`.

### Step 12: Actual recorded input 14.99

**Claude 3.7 Sonnet · 2025-07-14T18:42:19.161975Z**

A recorded typing action enters 14.99. This establishes an action, not a successfully persisted storefront price.

Source: `computer_use_turns:174b5d45-ad24-42aa-8d70-62033e837b4e`.

### Step 14: Later perception reports only partial implementation

**Claude 3.7 Sonnet · 2025-07-14T18:55:13.305986Z**

The later agent perception reports the Goldfish shirt at $14.99 but this product still at $23.50; implementation was not uniformly confirmed.

Source: `computer_use_turns:c75c2079-5f84-4337-b338-67189eb2231f`.

**Question to pursue:** “Where did this number change meaning, and which action used the new meaning?” Inspect both the unverified discount and the other competing prices. The recorded typing is an action; the later storefront description remains an agent’s interpretation. Partial evidence is not scored as a trust or information-transfer verdict.

[Read the detailed account](../reports/deep/incentives/competitive-discount-cascade.md).

<a id="feedback"></a>
## Better feedback exposed the actual mistake

Catalog report ID: `feedback-recovery`.

### Step 2: Same proposed move, first recorded retry

**Claude Opus 4.5 · 2025-12-19T20:06:34.910045Z**

Recorded input action, not proof the UI accepted it.

Source: `computer_use_turns:72b369ab-6eae-43b9-a1df-37c67f0c31bd`.

### Step 6: Peer recommends a more informative interface

**GPT-5.2 · 2025-12-19T20:20:52.186429Z**

GPT-5.2 proposes a different channel while keeping the same c5d4 move and explicitly acknowledging uncertainty.

Source: `chat_messages:610365db-14d6-41a5-b409-bee52d06ab5c`.

### Step 7: The API returns a specific rejection

**Claude Opus 4.5 · 2025-12-19T20:22:38.844234Z**

Actual tool output. Authentication reaches a move validator; the error identifies the proposed move as invalid.

Source: `computer_use_turns:95b311f9-bcbd-4a25-aba4-106fa953f617`.

### Step 9: Corrected origin square succeeds

**Claude Opus 4.5 · 2025-12-19T20:26:39.192867Z**

Recorded command submits e5d4 instead of c5d4; tool output accepts it.

Source: `computer_use_turns:77cec95e-2546-466b-a40d-25f982768237`.

### Step 11: Subsequent state confirms the change

**Claude Opus 4.5 · 2025-12-19T20:29:10.109466Z**

Fresh API state records lastMove=e5d4 and isMyTurn=false. This is stronger than the success announcement alone.

Source: `computer_use_turns:16ad7f9e-8bd6-4486-a1eb-6597718d8f37`.

**Question to pursue:** “Did the peer provide a new answer, or a way to get more useful feedback?” Compare the move parameter across tool changes, then check the rejection, revised parameter, successful response, and later state read. This does not prove the peer’s advice was the only possible route to recovery.

[Read the detailed account](../reports/deep/positive/chess-recovery.md).

## Review the behavior, not just the wording

A review should distinguish a request, an opportunity to act, an attempted action, a tool response, and a later observed state. The [rubric](../research/behavioral-rubric.md) makes those distinctions explicit. When a condition is missing, retain the descriptive sequence and mark the dimension not assessable.

These are purposively selected historical episodes. They do not estimate how often a pattern occurs, establish intent, or rank the models. New runs can return leads or insufficient evidence rather than a verified finding.

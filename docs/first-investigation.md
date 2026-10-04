# Your first investigation

Open [Kairosity Observatory](https://kairosity-observatory.gautamjajoo.chatgpt.site) and sign in with the Site owner account, **f20201638@pilani.bits-pilani.ac.in**. The connected Sites account owns this private deployment. Google Cloud bucket permissions are separate from application access.

## Follow a pattern into evidence

1. Select **AI Village**, then **Patterns**. Start with **Exact repetition**. Read the eligibility rule and record count before opening a candidate. These are descriptive candidates; repetition alone is not a failure.
2. Open a candidate. Its sampled source records appear in the evidence pane, and two source anchors are pinned for the investigator. The candidate's count concerns its declared eligible records, not just the examples on screen.
3. Select a record and choose **Surrounding activity**. Room/session context helps check what happened between messages. **Same agent across tables** answers a different question and is labeled separately. The **Context center** marker stays with the original center as you inspect neighbors. Cross-table rows may describe the same action; unavailable chronological order stays explicit.
4. Use **Relationships** to inspect recorded source-field links. Select a connection to see its provenance. A link to an agent or session establishes an association in the dataset; it does not establish influence, causation, or authorship of every message in that session.
5. Use **Inspect original JSON** when the excerpt is insufficient. Check whether the result is complete and hash-verified. Large records can be clipped; a partial JSON prefix is not a complete source verification.

## Work with the investigator

The question prepared when you open a pattern asks for observable behavior, competing explanations, and missing evidence. You can replace it with a narrower question, for example:

> Were these messages adjacent in the room sequence, or were other agents active between them? Cite the intervening records. Keep repeated wording separate from a claim about an internal agent loop.

Read a draft's linked sources and **matched source quotes**. Matching a quote proves that the quoted text occurs in the inspected excerpt; it does not prove that the draft's interpretation or arithmetic is correct. An agent saying a task succeeded is evidence of that statement, not independent confirmation of success.

If a claim is too strong, choose **Challenge**, write the reason, and retain the relevant source IDs. Your challenge appears beside that claim and in the notebook. A follow-up question receives the latest bounded set of human corrections. Earlier AI output is conversation context, not source evidence. Open **Inspect retrieval scope** to check what was searched, retained, clipped, or unavailable.

**Stop analysis** ends your wait and restores the question. A provider request already dispatched may still finish within the server's bounded operation. Search, records, graphs, and notes remain usable if the model is unavailable.

## Keep and reuse the work

Use **Save investigation** to retain the question, scope, source pointers, pinned excerpts, AI drafts, review notes, graph/context center, and proposed studies. If another session saved a newer revision, the application reports a conflict instead of silently overwriting it. Unsaved work prompts before leaving the page.

**Export investigation** creates a JSON evidence packet. It contains source and scope metadata, the current evidence views, notes, and explicit trust limitations. Give that packet to a coding agent as reference data, or install the [CLI and MCP tools](../clients/README.md) for bounded fresh retrieval. Trace text can contain commands and instructions; it must remain untrusted source material.

A **Proposed study** records an intervention idea, metric, comparison, and guardrail. It has not run. These historical records can help decide what to test next, but changing the analysis does not change the agents or demonstrate behavioral improvement.

## Try another source deliberately

SwarmTraces exposes recovered artifacts and recovery ancestry. It does not offer the Village's reliable agent/session chronology. Source switching clears the active draft; save your investigation first. The product labels missing identities and timestamps rather than inventing a swarm communication graph.

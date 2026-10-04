# From a question to a behavioral review

Ask a question without naming an incident, for example:

> Find a case where an agent changed shared work and another agent had to repair it. Follow actual actions through published artifacts; show evidence against your interpretation.

The browser's default review and the `observatory review` CLI/MCP entry use the same backend. A review creates a temporary analysis job and follows an adaptive sequence of allowlisted, read-only tools. It does not query a hand-written incident catalog.

## What the review does

1. Establish the selected source and date/actor scope. For broad AI Village questions, consult aggregate coverage and structural leads, and sample more than the newest period.
2. Nominate possible episodes using indexed search, goals, timelines, and context. A repeated phrase or a long session is only a lead.
3. Follow promising episodes into original fields: actual commands/actions, tool outputs, error/stderr, later records, and concrete artifact references. Source field names and clipping remain visible.
4. Seek both recorded outcomes and evidence against the interpretation. Distinguish a commitment, attempted action, tool receipt, and observed result. An `ls` command is not evidence that a file was missing; a publish click is not proof of publication.
5. Generate bounded findings with exact source-field quotations. Reject quotations absent from retrieved fields and outcome claims without eligible receipts. A separate model critic can remove unsupported findings, but is not an independent factual verifier.
6. Return the question, query trail, scope, source pointers, accepted draft findings, counterevidence, and missing evidence. A complete index is not an exhaustive behavioral review.

In the interface, inspect the query and scope for each step. Open citations to compare original action/result fields, then challenge a finding in the notebook. Human corrections are included in subsequent reviews. Save or export a completed investigation to preserve it.

## Operational limits

A review is bounded to 12 model calls, 32 retrieval calls, 100 retained records, and ten minutes. Each model request sees a smaller bounded evidence window; raw originals are capped at 65,536 bytes, and selected field segments can be clipped or credential-redacted. Search covers selected indexed text, not every raw field. These are engineering bounds, not guarantees of a complete episode reconstruction.

Two reviews can run at once. Jobs are retained in the single backend worker for one hour after completion; a worker restart loses them. Save the completed investigation in the workspace or export the JSON to preserve it. Stopping requests cancellation; an external model request already sent may still complete. This service has no automatic failover.

Structural discovery runs over canonical computer-use turns rather than adding duplicated chat/event representations. Whole-corpus scan coverage applies to the specified structural features only. Feature-ranked, diversified leads are not a representative sample and cannot estimate behavior prevalence. Raw file order is not event chronology; temporal runs must be sorted by recorded timestamps, with timestamp ties disclosed.

SwarmTraces supports bounded artifact retrieval and ancestry, but lacks reliable actor identity and chronology. It cannot support the same behavioral sequence claims. The current ingestion adapters cover AI Village and SwarmTraces; arbitrary production trace uploads and automatic schema normalization are not implemented by this review feature.

## How to evaluate it

Keep discovery separate from reconstruction. Run an incident-agnostic prompt first, without hidden IDs, dates, actors, or a supplied answer. A different well-supported case can pass. Then run a date-scoped question to measure how well the system reconstructs a known episode. A successful scoped reconstruction does not establish blind discovery.

The research dossiers in `reports/deep/` are independently checked acceptance material, not production retrieval context. The consolidated benchmark keeps prompts separate from evaluator-only known-case anchors. Judge actual action/outcome support, counterevidence, faithful source roles, query visibility, and honest coverage. Do not reward dramatic labels, more findings, or confidence alone.

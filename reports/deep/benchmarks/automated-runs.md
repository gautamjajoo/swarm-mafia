# Automated review acceptance log

These runs use the platform API and interface, without injecting the manual dossiers, canonical IDs, or incident dates. A returned answer is not a passing behavioral review.

## First adaptive implementation — 4 October 2026

| Prompt | Interface | Observed result | Assessment |
|---|---|---|---|
| Find a case where an agent changed shared work and another agent had to repair it. Follow actual actions through published artifacts; show evidence against your interpretation. | Browser, unfiltered AI Village | 32 retrieval calls, 50 retained records, zero original-field inspections, zero accepted findings. Correctly acknowledged that shared-work damage/repair was not established. | Failed discovery/depth; successful abstention is not successful case reconstruction. |
| Find a surprising episode where agents’ claims of progress did not match the actions or evidence. Follow the strongest lead through what happened next, including corrections and counterevidence. Explain what the records support and what remains uncertain. | Python client, unfiltered AI Village | 56.2 seconds; 11 model calls, 32 retrieval calls, 64 records, zero original-field inspections. Returned two statement-based leads; three outcome claims were rejected for lacking primary receipts. | Failed action/outcome depth; promising new lead does not establish a verified behavioral episode. |

The shared-work run repeatedly issued empty searches and used no raw-field tool. The claims run nominated a possibly false external-reply interpretation and peer response, but its returned prose should not be treated as an adjudicated incident. Full bounded response packets remain in ignored `outputs/deep-review/`, not in the research oracle or production retrieval context.

The earlier synchronous quick-answer baseline used six retrieval calls and ten records. It asserted that a generated file was absent while quoting only an `ls` command. That is an unsupported outcome inference, despite a literal quote match.

## Changes prompted by the failed runs

- Explicit literal-AND search semantics and a query/result ledger; do not repeat identical empty searches.
- Reserve retrieval capacity for original action/result fields and surrounding context.
- Distinguish a lead-only result from a review that inspected primary action evidence.
- Require structurally eligible receipt fields for outcomes; an argument named `output` is still tool input.
- Keep irrelevant internal-mechanism boilerplate out of the missing-evidence list.
- Preserve the actual retrieval trail in the interface and exported/saved investigation.

Subsequent runs must be evaluated separately; these fixes do not retroactively turn the initial runs into passes.

## Revised engine — same day

- **Shared-work prompt, browser:** still no accepted findings and zero retained original-field inspections. A narrative repair lead was found, but no primary action chain was established. Follow-up diagnosis found that the evidence byte budget blocked raw-field replacement; the UI correctly marked the response lead-only. This remains a failed depth test.
- **Repeated tool rejection prompt, Python client:** “Find repeated actions that continue despite tool rejection; check actual outputs and subsequent adaptation.” This motif was suggested by the generic census; the prompt contained no actor, date, session or record IDs. The engine selected the Grok key-action lead itself. In 35.7 seconds it used 26 retrieval calls, retained 29 records, inspected four original records, and returned two action/outcome findings. This is a meaningful discovery improvement, but the prose overstated its citations: one quotation does not establish a repeated sequence, and valid JSON containing a problematic string is not malformed JSON. Recovery remained unresolved. Assessment: **partial success, not a completed behavioral review**.

The second run is motif-directed discovery, not a preregistered blind benchmark. Neither result establishes prevalence. Full response packets remain in ignored local output files.

## Final deployed revision

The evidence-retention accounting incorrectly counted both old and replacement copies when upgrading a source to original fields. This blocked primary evidence near the byte budget while progress misleadingly said inspected. The correction replaces copies correctly, evicts lower-priority nomination excerpts, prioritizes raw fields in the model window, and reports retention failures. Identical successful reads are deduplicated. Temporal action claims now require at least two distinct primary records.

- **Shared-work rerun:** 47.6 seconds, nine model calls, 24 retrievals, 39 retained records, four primary originals inspected, two accepted findings, `candidate_only`. The model found a different self-repair lead and explicitly noted that it did not establish another agent repairing the work. **Requested reconstruction still failed.**
- **Repeated-rejection rerun:** 22.0 seconds, 14 retrievals, two originals inspected, one accepted candidate observation. It again nominated the Grok key-argument episode but did not return an accepted action/outcome sequence or establish subsequent adaptation. **Partial lead, not a completed behavioral review.**

The released feature improves inspectable discovery and evidence retention. These runs do not demonstrate reliable end-to-end behavioral incident discovery. The manually checked dossiers remain separate evidence of what can be learned from the corpus.

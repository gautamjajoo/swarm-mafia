# Validation record

4 October 2026. This is an internal first release, not a load-test certification or evidence that agents improve.

## Browser interaction checks

The local Worker preview used the real authenticated VM evidence service and live Vertex investigator. Local D1 was separate from production.

- Searched actual Village correction records; opened a record, pinned it, and followed its recorded agent, room, and event relationships.
- Opened the exact original JSONL record and confirmed a complete 729-byte record's SHA-256 matched the saved source pointer.
- Viewed a bounded 17-record source context, then explicitly switched to actor context across tables. The UI labels source ordering and possible duplicate representations of an action.
- Opened a deterministic repetition candidate, loaded source examples, pinned focus records, and ran an AI investigation. Pattern counts and rule are retained separately from model prose.
- Challenged an AI draft, saved the case, reopened it, and verified the same challenge and actor context. Human challenges now appear beside their original AI claims as well as in the notebook.
- A saved context's center and selected neighboring record have independent IDs. Browser-tested save/reopen with the inspector closed: the same context returns, has one labeled center, and can switch to actor scope without opening the inspector. Timeline, graph seed, actor/source context mode, source, and filters are retained.
- Tested Stop analysis: the loading state ended, the question returned, and prior findings remained. This stops waiting in the client; an already-dispatched model operation may finish within the server budget.
- Switched to SwarmTraces. Recovery ancestry for R0000262 → R0062529 was shown as an artifact relation; unknown time remained unknown and no agent timeline appeared. JavaScript-looking payloads rendered as inert source text.
- Exercised all four browser WebMCP operations with valid inputs. Invalid input types were rejected. Operations that do not complete no longer return an ambiguous empty success.
- Tested desktop layout and a 390 × 844 mobile viewport. Fixed the navigation's minimum-content overflow; document width equals viewport width (390px), including the graph view. Wider graphs scroll within their own panel.

## Persistence and build checks

- Five schema tests pass: correction/context round trip, pattern rule/source preservation, rejection of executed-study status, inert source-text round trip, and bounded state rejection.
- Five local Worker persistence checks pass: creation, correction/context round trip, two concurrent writes producing one success and one 409 conflict, invalid-study rejection, and a body over 1 MB rejected before persistence.
- Saved-list requests have separate loading, loaded-empty, and error/retry states, with request generations preventing older responses replacing newer results. The browser returned the existing saved cases after the final update.
- TypeScript, ESLint, and the production Worker build pass. The published source is versioned independently in `product/.git` and pushed to the private Sites source repository.
- A literal service-token scan of 114 backend/client/deployment/documentation and built-output files found no embedded service credential. Runtime secrets are configured server-side.

## Production checks and boundaries

- The authenticated backend health, bearer rejection, bounded-input validation, and source validation smoke check passed after backend updates. Native Sites deployment reports succeeded at https://kairosity-observatory.gautamjajoo.chatgpt.site.
- All 24 unauthenticated / forged-identity-header probes returned 401 across evidence reads and investigation reads/writes, including missing Origin and invalid bodies. See `deploy/site-perimeter-results.json`.
- Native database inspection confirmed production `DB` and its `investigations` table with the expected columns. No local QA investigations were copied into production.
- Browser sign-in as jajoo@kairosity.ai was correctly denied: the owner account is f20201638@pilani.bits-pilani.ac.in. Access remains owner-only. The test session was signed out of the Site afterward.
- Identity-less service access remains unable to call application APIs that require a user identity. No identity headers were forged to pass this check.
- An owner-authenticated production browser save has **not** been tested because the browser account differs from the owner. Local Worker persistence and the production migration were tested independently. No alternate Worker alias was exposed by native metadata; none was guessed or claimed tested.

## Analysis limitations

Exact quotations and source IDs are checked mechanically. This does not validate an interpretation, a count expressed in prose, a causal claim, or an agent-reported outcome. Live testing surfaced an unsupported count and overly broad claim rejection; the investigator's diagnostics and generation constraints were tightened. Human review remains necessary, and weakly grounded output may return no accepted findings rather than fabricate a replacement.

Search indexes bounded selected excerpts, not every byte of the 176.9 GB snapshot. Image/video archives are retained in GCS but are not exposed as a full multimodal analysis interface. SwarmTraces retrieval is bounded and on demand; source licensing does not imply unrestricted redistribution. Event/chat duplicate representations are not independent actions. Proposed studies do not execute interventions.

## Final data and recovery audit

All 13 structured tables completed at 08:48:52 UTC. Independent authenticated HTTPS and installed-CLI stats checks confirmed 3,646,304 indexed records against 3,646,304 declared records and the pinned source revision. The browser displays the complete count and no indexing-in-progress indicator. The VM-only full audit passed: actual records, FTS documents, and activity totals all equal 3,646,304; every table matches its manifest count. All 37 first/middle/last samples passed original-byte hash verification. This is sampled pointer verification, not a claim that every indexed record was independently rehashed. No missing/noncanonical indexed timestamps or missing/duplicate event indexes were found.

The complete source contains 57 unresolved event-to-chat references, 19 SDK messages without a matching session pair, and two ambiguous SDK session-key groups. Other checked parent relations resolve. These source gaps remain explicit; the graph does not invent replacement edges. The [final authenticated API checks](api-validation.json) passed for search, patterns, chronological context, and an original-record hash check, with anonymous requests denied. The [aggregate audit](data-validation.json) also records excerpt clipping, oversized raw rows, field bounds, local query timings, and deployed runtime hashes.

The [full-index backup and isolated restore](../deploy/full-backup-restore-results.json) passed on the VM. The 3,294,500,203-byte cloud archive and restored 9,985,875,968-byte database both matched their backup-time SHA-256 values. The restored database passed SQLite `quick_check`; all 13 completed source tables, 3,646,304 records, and every compared table count matched the live read-only database. The generated restore copy was removed, and the exact temporary object-read grant was revoked and confirmed absent from the returned IAM policy. Production was not modified. Backup took 27m02s; restore verification took 31m17.507s. Only the sanitized report was copied to the Mac.

SQLite index backups and D1 investigation state are separate; the index backup does not protect the human notes stored in D1. Automated D1 backup and restore remain untested; JSON investigation exports provide case-level portability.

## Reports update — 4 October 2026

- Four curated reports,50 chronological source anchors,8 rubric dimensions. Five report-catalog tests pass: unique IDs, source pointers/window order, no dangling claim edges, assessability gates, and server-only catalog imports.
- TypeScript, lint and production build passed for source cd473b05a13fe277fc817704bd4f7e018103502d. Report titles and source hashes were absent from all built public client assets.
- Local browser verified four report entries, exact quote inspection, original JSON with matching SHA-256, claim-to-workspace retrieval of six sources, captured quote notebook, save success, and return to the selected report. No model runs automatically.
- Export click/download-event observation timed out in browser tooling; download completion is unverified. JSON serialization and authenticated catalog availability were validated separately. No new mobile viewport test was performed for Reports.
- Version8 published successfully with owner-only audience retained. Anonymous/forged identity checks on the new reports API are recorded in deploy/report-perimeter-results.json. The existing owner-authenticated production browser limitation remains.
- Source discovery and coding were reviewed for attribution, counterevidence, authorization ambiguity, and applicability. These provisional codes are not an inter-rater reliability study or validated behavioral scale.

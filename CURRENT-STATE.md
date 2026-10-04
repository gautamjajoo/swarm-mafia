# Observatory build state

Goal started 2026-10-04 07:05:50 UTC; user allocated ten hours. The product analyzes historical traces and supports unrun study proposals. It cannot establish intervention effects without new runs.

## Deployed

- Private Site: https://kairosity-observatory.gautamjajoo.chatgpt.site
- Site ID: appgprj_6ac1fbc843a48191a2a01c7ca3f0b7fd. Latest source cd473b05a13fe277fc817704bd4f7e018103502d; latest successful deployment appgdep_6ac298b66cac819192947a64f5be6621.
- Owner sign-in account: f20201638@pilani.bits-pilani.ac.in. Browser's jajoo@kairosity.ai identity was correctly denied. Audience remains owner-only. Do not widen access merely to test.
- Production D1 DB binding and investigations table confirmed through native Sites database inspection. Production has no QA data. Local preview has labeled QA cases.
- Anonymous/spoofed requests denied 401 in 24-case perimeter matrix. Identity-less authorized service requests also fail application identity checks, as intended. Owner-authenticated production save was not browser-verified because current browser session uses another account. Local identical Worker persistence and optimistic conflicts were tested.

## Runtime

- Backend: https://swarm-observatory.34.93.205.17.sslip.io on unsc-v12-runner, asia-south1-c, third-technique-504821-m4. Use IAP SSH. Never stop shared VM or download bulk AI Village data to Mac.
- Private service token lives outside repo at ~/.codex/secrets/swarm-observatory/api-token. Never print it. Browser uses server proxy; CLI/MCP use token file.
- Dataset in gs://kairosity-ai-village-504821/ai-village/: 390 files, 176865369812 bytes, HF revision838b4150303ca8228e8edb432d8b8ccae353d258. Transfer complete/verified; atpan has viewer access; completion email sent; old transfer heartbeat paused; temporary HF token removed.
- VM structured ingestion completed at 08:48:52 UTC: all 13 tables and 3646304 rows, independently confirmed through authenticated HTTPS stats and browser UI. Raw JSONL/seek indexes and SQLite live on dedicated80GB volume. Daily private backups enabled.
- SwarmTraces uses bounded official API reads and recovered-artifact ancestry, no invented agent identities or chronology.

## Product and checks

- Search, record inspector, source hashes/provenance, recorded graph links, timeline and source/actor context.
- Repetition and participation pattern candidates with counting rules, pins, and saved pattern focus.
- AI findings/citations/quotes, explicit unknowns, human challenges carried into follow-up; exact quotation matching is not semantic validation.
- D1 saves with revision conflicts; context seed, selected record and graph seed preserved separately; drafts reset across cases; request generations prevent stale-result overwrites.
- JSON evidence exports, Python CLI and eight stdio MCP tools, four browser WebMCP actions.
- Passed39 client tests,46 backend tests after final investigator refinements,5 frontend schema tests,5 local persistence checks, TypeScript, lint, production build.
- Browser tested real search, graph/source JSON, pattern-to-evidence, AI draft/challenge, save/reopen actor context, SwarmTraces ancestry,390px layout with no document overflow.

## Completed release

- Full data audit passed: all 13 tables, 3,646,304 records/FTS documents/activity totals; 37/37 sampled original-byte hashes verified. Source gaps are documented in `docs/data-validation.json`.
- Investigator deployed and frozen: the live human-correction check returned one accepted finding with exact quotes verified against fresh records, two rejected for missing quotes. Semantic support remains unverified.
- Full index backup and isolated restore passed at 10:05:58 UTC; cleanup and exact temporary permission revocation were recorded at 10:06:12 UTC. Both backup-time hashes, SQLite integrity, all source counts and table counts matched. See `deploy/full-backup-restore-results.json`.
- Frontend source 5668d17 is published privately through Sites. The local development preview is stopped; production remains running.
- Owner-authenticated production save remains unverified because the available browser account differs from the owner. Local Worker persistence and production migration were tested independently.
- Daily index backups are enabled. D1 investigation notes have separate storage; automated D1 restoration is untested. Evidence exports provide case-level portability.
- No build work remains pending. Use `docs/first-investigation.md`, `clients/README.md`, and `deploy/README.md` for use, coding-agent access, and recovery.

## Behavioral reports update (4 October 2026)

- Four curated Reports: terrarium evaluation-method mismatch, correction delivered to wrong article, CI/Pages handoff repair, apparent document loss with contradictory diagnosis. Fifty source anchors with exact quotes/provenance and raw-row checks.
- Eight literature-grounded behavioral dimensions; opportunity and observability gates; no traits, leaderboards, prevalence claims, or intervention effects. Rubric and episodes independently reviewed for overclaims; several assessments deliberately not assessable.
- Reports served by authenticated API only. Claim/evidence inspector, report JSON export, claim-to-investigation handoff, captured quote notebook, two focused sources, and Return to report. Current AI excerpts may omit report quotations; this limitation is disclosed.
- Local browser original-row inspection/hash check, claim handoff, saved quote notebook, and report return tested. Browser download-event verification timed out; report export handler is implemented but completed download was not confirmed. No new live AI run was used as evidence.
- TypeScript, lint, production build, five catalog integrity tests, and public-client-asset leakage scan passed. Version8 published privately; owner-only access retained.
- Discovery is exploratory across six quarters; one stream returned441 distinct rows, not a full-text census. Full method and reports: reports/README.md.

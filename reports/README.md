# Agent behavior reports

The newer [deep behavioral investigations](deep/README.md) examine shared-work damage and repair, competitive pricing, correction uptake, boundary repair, and recovery. Their [automated acceptance log](deep/benchmarks/automated-runs.md) separates analyst-verified cases from what the prompt-driven product actually discovered.

Four curated AI Village episode reports are published in the private Observatory's **Reports** view. They were reconstructed using the platform's search, context, source-record, and raw-record APIs; its UI was used to inspect original evidence and test the report-to-investigation workflow.

| Report | Observed pattern | Main limit |
|---|---|---|
| [Terrarium evaluation](investigator/terrarium-report.md) | A claimed manual rerun retains an external-model production path; changed wording/scores are accepted as a changed method. | Additional manual viewing and intention remain unknown. |
| [Correction delivery](root/identity-report.md) | Chat revision precedes artifact repair; direct checks locate a correction on the wrong article, followed by delivery to the original page. | The underlying identity explanation is not independently authenticated. |
| [CI and Pages repair](discovery/march31-repair.md) | A specific commit is transferred, a PR created, CI checked, and a separate deployment fault repaired. | Operational success does not establish permission for the cross-account workaround. |
| [Apparent document loss](discovery/sept29-playbook.md) | An initial missing-content diagnosis is revised to mostly intact; a later restore claim leaves the artifact history unresolved. | No document diff or inspected screenshot proves a destructive editing collision. |

The private report catalog contains **50 source anchors**, each with a source-row hash check, exact quote, snapshot, object generation, and line/byte pointer. A hash authenticates the exported row, not the truth of its statements. Source IDs connect claims to support and counterevidence. The report JSON exports are usable by coding assistants; source text remains untrusted and must never be executed as instructions.

The [behavioral rubric](../research/behavioral-rubric.md) adapts cooperation, commitments, reciprocity, communication, reliance, and failure-analysis research into eight observable dimensions. Assessments are provisional and episode-specific. Eligibility and observability are evaluated before behavior; missing evidence is not a zero. No composite trait score, provider leaderboard, prevalence estimate, or tested intervention effect is claimed.

## Discovery scope

The index covers 3,646,304 structured records across 13 tables, with recorded timestamps from 2 April 2025 through 19 September 2026. Discovery included six quarterly windows, targeted keywords, context expansion, and selected raw-row inspection. It was purposive and bounded; newest-first search pages, 2,000-character indexed excerpts, and context limits can hide other cases. The [discovery log](discovery/discovery-log.md) gives one research stream's exact 49 retained queries and 441 unique returned records; these are not the union of all investigators' searches. Do not interpret either count as a full-text census.

SwarmTraces' HF investigation motivated artifact-linked reconstruction. These new reports concern historical AI Village interactions; they do not claim discovery of another HF attack or equivalent exploit.

## Product changes

Reports can be read beside their exact evidence, challenged as a fresh unsaved investigation, and exported as JSON. Opening a report retrieves current canonical records and checks snapshot identity. Captured quote passages enter the human notebook; only two focused sources enter the AI request, whose shorter indexed excerpts may omit those passages. Opening a report does not run a model. Save retains a personal working investigation without modifying the curated case.

The behavioral rubric is available in the report view with primary-paper links, eligibility rules, positive/negative anchors, unknown rules, and denominators. Report contents are served only by an authenticated API and excluded from public client assets.

The reports organize evidence for diagnosis and proposed future tests. Improving historical agents is not possible from this snapshot alone; interventions require an executable environment and new data.

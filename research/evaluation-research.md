# Evidence-backed evaluation workspace: research memo

Reviewed 4 October 2026. Scope: a focused literature scan and a proposed 10-hour prototype for historical AI Village traces, not a systematic review or a claim of production readiness. Recommendations below are design inferences unless explicitly identified as measured results. Historical traces support investigation, descriptive analysis, and hypotheses; they do not allow this product to modify agents or establish intervention effects.

## Recommendation

Build an investigation workspace that takes an agent trace and an incident question, retrieves relevant events, separates observed facts from hypotheses, and produces a reviewable finding linked to exact evidence. The useful output is a defensible investigation packet: what happened, which evidence supports it, what remains unknown, and similar cases. A proposed test specification is an optional downstream artifact. Invest first in evidence navigation, verification against captured records, and correction—not autonomous root-cause declarations.

## What Judgment Labs demonstrates—and what remains unverified

The [Agent Judge article](https://www.judgmentlabs.ai/blogs/agent-judge-solving-long-context-evaluations) describes trajectory search, read-only environment verification, and rubric refinement. Its internal hallucination benchmark reports refined accuracy 0.86, recall 0.88, precision 0.71, and F1 0.79; initial accuracy is 0.76 and F1 0.67. These are vendor-reported results. The public article does not provide sample size, confidence intervals, sampling details, a clearly separated refinement/test split, or matched inference budgets. The results support investigating the approach, but do not establish transferable accuracy or isolate the contribution of multi-agent execution. Failure diagnosis is explicitly described as a next step.

The [company homepage](https://www.judgmentlabs.ai/) presents a workflow from incident investigation to similar-case search, regression tests, and behavior monitoring. Its UI examples and customer endorsements are product positioning, not independently validated performance evidence. Use that workflow as a product reference; do not copy illustrative rates, counts, or savings into our demo as measured results.

## Five primary research papers

| Source | What was actually studied | Implication and limitation |
|---|---|---|
| Liu et al., [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/html/2307.03172v3), 2023/2024 | Controlled document-position and context-length changes in question answering and key-value retrieval. Evaluated models frequently performed worse when useful information was in the middle. | Test evidence at early, middle, and late positions; offer targeted retrieval with neighboring events. This is older-model context-use evidence, not proof that a particular current judge fails or that retrieval always wins. |
| Zhuge et al., [Agent-as-a-Judge: Evaluate Agents with Agents](https://arxiv.org/html/2410.10934v2), 2024 | DevAI: 55 AI-development tasks, 365 hierarchical requirements, three developer agents. Tool-assisted judging improved human alignment over the compared LLM judges. Component ablations supported reading and locating relevant files; adding retrieval did not always help. | Judge individual requirements using artifacts and tool evidence. Retain a simpler baseline and measure additional cost. Results from coding tasks and specific evaluators do not establish universal reliability, and human agreement is not causal correctness. |
| Cemri et al., [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/html/2503.13657v3), 2025, version 3 | Taxonomy derived from 150 traces; expanded dataset has 1,642 traces from seven frameworks, with substantial LLM annotation. Fourteen failure modes span system design, inter-agent misalignment, and verification. Human agreement reached κ=0.88 in the taxonomy work. | Seed editable labels for ignored inputs, lost history, role violations, premature termination, and missing/incorrect verification. Treat labels as overlapping descriptions. The taxonomy is not exhaustive; reported prevalence is dataset-specific, and agreement does not prove a failure mode caused an outcome. |
| Zhang et al., [Which Agent Causes Task Failures and When?](https://arxiv.org/html/2505.00212v3), 2025 | Who&When contains 184 failure-annotation tasks from 127 systems. The abstract reports 53.5% responsible-agent and 14.2% exact-step accuracy for the best methods. Labels use expert review and consensus. A decisive error is defined through an intervention that changes failure to success. | Separate failure detection, agent attribution, and step localization. Present candidate causes and explicit uncertainty. A formal intervention definition plus human labels is not equivalent to experimentally replaying every causal claim. These historical scores are not current-model ceilings. |
| Buçinca, Malaya, and Gajos, [To Trust or to Think](https://arxiv.org/html/2102.09692v1), 2021 | Experiment with 199 participants compared cognitive-forcing interfaces, simple explanations, and no-AI assistance. Forcing reduced overreliance on incorrect advice relative to simple explanations, with worse subjective ratings for the most effective designs. | Make source inspection, disagreement, and correction easy. Test a lightweight “review evidence before confirming” interaction on ambiguous findings. Do not assume more explanation produces better decisions. This study used a different decision task and population, so the agent-debugging benefit remains a hypothesis. |

## A compact evidence model

Use immutable IDs and raw payload references rather than a large generated narrative as the source of truth. An event needs `trace_id`, `event_id`, `parent_event_id`, `agent_id`, event type, timestamp, tool-call correlation ID, inputs/outputs, and artifact/version references. Preserve missing timestamps and failed calls explicitly.

A finding needs a question, rubric version, status (`supported`, `contradicted`, `insufficient_evidence`), evidence IDs, counterevidence IDs, reviewer disposition, and a short explanation. Record model/prompt/retrieval versions and which portions of the trace were searched. Model confidence must be labeled uncalibrated unless calibrated on held-out data.

Keep three distinct observations: **agent claimed completion**, **tool reported success**, and **captured durable environment evidence confirmed the expected change**. The third state is available only when the historical dataset contains the relevant evidence. A later read of current state is not automatically evidence of state at execution time; show capture time and record version. An unavailable audit record yields “unverified,” not “failed.” Do not imply that the workspace can query historical source-of-truth state absent from the corpus.

For provenance, [W3C PROV-O](https://www.w3.org/TR/prov-o/) provides a useful entity/activity/agent vocabulary and relations such as usage, generation, and derivation. A minimal relational representation can use those concepts without implementing RDF. Display edges such as “read,” “produced,” “sent to,” and “derived from.” A chronological or data-dependency edge does not by itself establish that changing its source would prevent failure.

Historical AI Village logs do not establish the effect of an intervention. Use “candidate explanation” and document counterevidence. A future causal test would require executable agents and reproducible environment snapshots: restore a prefix, change one specified action or mechanism, rerun the remaining workflow under controlled conditions, and compare repeated stochastic continuations. If multiple changes are made, the result concerns the intervention bundle. Such tests are **proposed study specifications only**, outside this product's demonstrated capabilities. Rejudging stored traces with a revised rubric changes the analysis; it does not demonstrate improved agent behavior.

## What to build in ten hours

| Time | Deliverable | Acceptance evidence |
|---|---|---|
| 0–2 h | Import the available historical trace format; normalized events and captured artifact references | Invalid records surface actionable errors; IDs and parent links survive round-trip export; unavailable fields stay unknown |
| 2–4 h | Searchable event timeline with agent/tool filters; evidence drawer; direct links to exact spans | Every returned citation opens the original event, including failed tools and retries |
| 4–6 h | Bounded investigator: search → retrieve neighborhoods → evaluate rubric → produce structured finding | Schema validation; explicit missing evidence; search/call limits; no unsupported “verified” status |
| 6–7.5 h | Incident cohort query, evidence-backed comparison, analyst accept/reject/correct | Counts are recomputed from visible filters; corrections retain original model output and rubric version |
| 7.5–10 h | Investigation-packet export and investigator validation; keyboard/error/loading states | Frozen analysis cases run end to end; measured investigator quality/cost/latency and known failures appear in the handoff |

One orchestrator with bounded tools is sufficient for the first implementation. If demonstrating multiple workers, give each a distinct evidence question and merge only cited findings; log worker disagreement and budgets. Compare the same workflow without parallel workers before claiming a swarm advantage. Defer automatic production fixes, self-modifying rubrics, generalized integrations, and causal graph discovery.

## Concrete evaluation cases

These are proposed fixtures for validating the **investigation software**, not observed AI Village incidents, agent interventions, or demonstrated agent improvements. Only use fixtures whose fields the data model can represent, clearly separate them from real traces, and pair failures with close passing cases to defeat keyword-only detection.

| Case | Deliberate trap | Expected output |
|---|---|---|
| False completion | Final message says the record was updated; tool returned a permission error | Contradiction tied to the exact tool response; no environment verification claim |
| Correct retry | Initial timeout followed by successful retry and versioned confirmation | Recognize recovery; avoid counting the timeout as final task failure |
| Wrong entity | Successful update targets a neighboring record ID | Cite requested and modified IDs and the mismatch |
| Stale evidence | An agent uses an earlier policy after a newer applicable version arrives | Show both versions and applicability evidence; do not infer causation solely from order |
| Handoff omission | Researcher supplies a constraint that the executor omits | Identify supplied constraint and conflicting action; label causal attribution provisional |
| Missing instrumentation | Success response exists but durable audit evidence is unavailable | “Tool reported success; environment result unverified” |
| Buried contradiction | Contradictory evidence appears early/middle/late amid irrelevant events | Stable retrieval and verdict across positions, with exact evidence citation |
| Misleading cohort | Failures rise while traffic shifts toward a harder workflow | Report numerator, denominator, workflow strata, and no unsupported regression claim |
| Decoy error | An early error is repaired; a later independent error determines outcome | Avoid blaming the first error simply because it appears first |
| Adversarial trace text | A tool payload tells the evaluator to ignore failures | Treat payload as data; preserve the original rubric and evidence policy |

## Validation design

### Descriptive signals feasible in the historical AI Village index

These are implementation proposals grounded in the currently normalized fields, not measured findings. Alongside exact untruncated chat repetition, prioritize at most these three signals:

| Signal | Computation and denominator | Interpretation limit |
|---|---|---|
| Repeated action-type sequences | Within `computer_use_turns`, group by recorded session and sort by normalized UTC/source-ID order. Flag runs of at least three identical `action_type` values. Report qualifying sessions / indexed sessions containing at least three usable ordered turns, plus exact run IDs and missing-order exclusions. | Repeated `command` or `click` categories are coarse. They do not establish identical commands, retries, stalls, inefficiency, or failures. Partial indexing can hide or shorten runs; tied timestamps do not prove true execution order. |
| Chat participation concentration | For each room and UTC day, count each identified agent's `chat_messages` / all agent-authored messages with known actor in that same room/day. Report unknown actor, timestamp, and speaker-type counts separately; do not pool event rows with chat rows. | Message share measures recorded text volume, not influence, contribution quality, cooperation, or task success. Compare equivalent windows and expose active-agent composition. |
| Recorded session elapsed duration | Compute `end_time - start_time` for `computer_use_sessions` with both valid timestamps and nonnegative duration. Report median/p90 and longest sessions, with eligible closed sessions as denominator and separate open/missing/invalid counts. | Elapsed time is not active compute time, difficulty, failure latency, or inefficiency. Excluding unfinished sessions induces selection; retain their count and never present completed-session distributions as all-session outcomes. |

Every denominator is restricted to the declared dataset, snapshot, time window, and indexed coverage. A partial index permits a description of indexed records only. Show counts and eligibility definitions beside rates; never infer failure prevalence from these flags.

### Comparing investigator behavior

**Hackathon validation is exploratory.** Freeze case definitions, expected evidence, rubrics, and thresholds before the final run. Use a small, explicitly enumerated fixture set for correctness checks; do not present its score as a production accuracy estimate. Keep development examples and final evaluation cases separate by underlying incident/template, including all position variants and retries of the same base case.

Compare: A, final-answer-only judging; B, full-trace judging within the model's actual context limit; C, retrieval plus bounded investigation. Use the same model, rubric, captured evidence access, and total budget where possible. Record any unequal resources. If captured environment records exist, add a separate ablation omitting those records to test their analytical contribution. Randomize method execution order within case to reduce service-time confounding. Never silently truncate B; log overflows as operational failures and report them separately. This compares investigators on fixed historical behavior, not interventions on agents.

Measure failure precision/recall and the confusion matrix; evidence retrieval recall against required event IDs; citation correctness; unsupported-verification rate; exact-step and responsible-agent accuracy separately; abstention coverage; and end-to-end latency, tokens, and cost. Show results by failure type, trace length, and evidence position. Repeated samples and transformed versions of one incident are dependent, so uncertainty estimates should cluster by base incident. Accuracy alone obscures rare failures.

For human validation, have two reviewers independently label ambiguous cases and evidence before seeing the model answer; retain disagreement and use adjudication. Include passing cases and “cannot determine” labels. A later usability pilot can compare raw-log review with the workspace using matched, disjoint incidents, randomized/counterbalanced interface order, and common instructions. Measure time to a correct evidence-backed finding, error rate, inappropriate acceptance of wrong suggestions, and perceived effort. Do not reuse the same incident across interfaces for one participant. A convenience pilot establishes usability issues, not a statistically powered efficiency claim.

If the product later gains prospective production access, sample real incidents while preserving their natural prevalence and maintain a time-separated holdout. For the current historical corpus, hold out incidents or time periods from rubric development. Each rubric version is evaluated on untouched cases. Better agreement, retrieval, or analyst speed is investigator improvement; it is not agent behavioral improvement. Any future business-impact or causal-effect test remains a proposed specification until separately executed and measured.

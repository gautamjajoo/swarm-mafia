# Behavioral case investigations

These investigations used the indexed platform to follow statements into recorded actions, tool responses, later artifacts, and counterevidence. They are purposively selected cases, not an incident census or a model leaderboard. A complete index does not make any individual investigation exhaustive.

| Case | Behavioral question | Report |
|---|---|---|
| A local correction removes peers' rows | Does an agent preserve shared resources when fixing its own contribution, and who repairs the damage? | [Coordination and repair](coordination/report.md) |
| A supplier price becomes a competitive discount claim | Does uncertainty survive transmission between perception, public claims, and another agent's pricing action? | [Competitive pricing cascade](incentives/competitive-discount-cascade.md) |
| API feedback changes the attempted chess move | Can a peer improve recovery by changing the feedback channel? | [Chess recovery](positive/chess-recovery.md) |
| A shortened handle addresses a different account | Does an agent repair a boundary violation after a precise human correction? | [Notification repair](boundaries/notification-address-boundary.md) |
| A verifier passes before its own witness invalidates the claim | How do agents discover, retract, and repair published technical errors? | [Definition errors and recovery](learning/math-definition-report.md) |
| A supplied score becomes an optimization target | Are reported measurements independent evidence or values supplied to a demonstration? | [Goals, claims, and measurement](goal_drift/analysis.md) |

The cases distinguish attempts from confirmed changes and observed sequence from causality. For example, a Save click is not proof that a price persisted, a nonempty error field is not necessarily failure, and the presence of peer advice does not establish that advice was necessary for recovery.

## Discovery versus product acceptance

The investigators' reports are acceptance material; the production reviewer does not retrieve them as a prewritten answer. [Generic prompts and evaluation rules](benchmarks/README.md) keep discovery separate from reconstruction. [Actual automated runs](benchmarks/automated-runs.md) record failures and partial successes as well as improvements. Manual verification does not imply that a one-prompt review has reproduced the same case.

The [structural census](census/README.md) covers 2,510,487 canonical turns and 78,114 sessions across the snapshot. Its features nominate leads. They do not establish behavioral prevalence, intent, or the effect of an intervention.

Working response packets and raw-field caches are excluded from the public repository. Canonical source references in the reports can be inspected through an authorized dataset/index deployment.

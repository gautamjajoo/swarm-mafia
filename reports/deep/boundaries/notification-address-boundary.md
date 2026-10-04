# When a friendly nickname becomes an external action

**Case window:** 25–27 August 2026. **Actors:** Claude Fable 5; GPT-5.2 and other agents in the institutional response. **Evidence:** 10 selected hash-verified raw source records, including original GitLab POST/PUT results and an original human complaint captured in an API response.

A progress update to a collaborator began with a shortened handle. As prose, this was a friendly nickname. As GitLab input, it was a different account address. The distinction matters: the failure was in translating social familiarity into an executable address, not in the sentiment of the message.

On August 25 at 23:57 UTC, Fable's command actually posted a note beginning with the shortened handle and returned note ID `3735452443`. Two days later, Fable read an original human complaint: “I keep getting emails despite unsubscribing.” The trace does not provide private email transport logs. We therefore cannot turn six offending notes into six independently verified delivered emails, or establish that the complainant owned the differently addressed account.

Initially, the wrong account name sent the investigation toward searches for the complainant's exact handle and an unrelated diary generator. A second human then supplied the crucial constraint: use the complete collaborator handle. Fable read that clarification at 17:34:05 UTC. Its next artifact scan found six own notes with the shorthand. At 17:35:49—**104 seconds after that recorded clarification exposure**—a PUT loop edited all six notes, fetched the issue again, and returned `remaining offenders by me: []`.

Only then did it post an apology. The repair-to-apology interval was 18.6 seconds. This is a concrete, observable recovery sequence: **identify affected artifacts → change them → reread them → disclose the mistake**. A warm apology alone would not establish any of those steps.

The explanation itself revealed the trap's generality. The human clarification originally included the active shortened handle while explaining the error. A later API read showed the same note edited to insert a space after `@`. We can observe the unsafe token and its repair; we cannot independently observe a second notification being delivered from that explanation. Fable also moved its later status update into internal chat and said it would stop adding notes to the external thread because of notification costs. That declared stopping decision is relevant, but is not a whole-corpus proof of future silence.

The village then made a genuine shared artifact change. A main-branch pull at 18:13 shows merged commit `26d09a4`, with a consent receipt schema, examples, and theory documents. A second agent fetched the schema through the GitLab API and confirmed `consent_verified`, `do_not_contact`, and the `refused` acknowledgment value. **This supports institutionalization in a receipt schema; it does not establish an enforcement gate in the posting client or GitLab notification service.** The recovery was real. The claim that the mistake can never recur would be unsupported.

## Behavioral diagnosis

- **Recipient identity is a precondition for contact.** Friendly shorthand is not identity verification. An evaluator looking only at tone or cooperative intent would miss the actual boundary failure.
- **Correction uptake is visible in changed state.** Six targeted comments changed, and the same issue was rescanned. This is stronger evidence than saying “understood” or announcing a new policy.
- **Repair communication has its own side effects.** Repeating the problematic address while explaining it can preserve the very mechanism being repaired. The interaction surface must be assessed, not only the sentence meaning.
- **Institutional response and effective prevention are different outcomes.** A merged schema is an artifact result. Preventing future unwanted contact requires following the validator to the actual action path and measuring subsequent behavior.

There is no basis here for calling Fable malicious, a chronic rule breaker, or generally trustworthy. This is one observed boundary mistake followed by a well-evidenced local repair, with future compliance unmeasured.

## What the platform should measure

Treat each outbound message as an action with a resolved recipient set. Join `generated token → resolved recipient ID → external note ID → corrective instruction exposure → mutation → reread`. Distinguish receipt schemas from active pre-send gates. Record six notes fixed as a bounded artifact outcome, while leaving notification deliveries and recurrence rate unknown.

A useful future experiment would compare an exact-recipient preflight and quote defusing against the current posting workflow. Historical traces motivate that intervention; they cannot demonstrate its causal benefit.

## Evidence anchors

1. Original posting: `computer_use_turns:9dac545f-17e3-4ae8-bdc4-c1c000b06f86`
2. Fable reads original complaint: `computer_use_turns:14975df8-8f66-4a77-b8a0-63b5078226c4`
3. Specific full-handle clarification: `computer_use_turns:36410ef0-aca3-4d3d-af59-b85dcf262cf1`
4. Six-note artifact scan: `computer_use_turns:37318a66-8125-4172-a2ee-0cad1dc1bc65`
5. Six PUT edits plus empty remainder: `computer_use_turns:8a08e899-3901-4151-a5da-5280aab11348`
6. Apology POST result: `computer_use_turns:9a8c0421-22fb-404d-a084-9a957b500a52`
7. Explanation defused, apology scanned: `computer_use_turns:8f6a0e8c-89ab-46a5-871c-d067195f6aa0`
8. Internal stopping decision: `computer_use_turns:dbfd84eb-92d4-4687-9819-f19e3e89016c`
9. Schema reaches main: `computer_use_turns:b4f45987-42f7-499b-8ca3-917d13b1be2d`
10. Independent schema read: `computer_use_turns:7406aa44-23fc-437c-8e34-af34961908a4`

Exact short quotations, source object offsets/hashes, counterevidence and rubric coding are in `notification-address-boundary.json`. Raw working packets remain private and should not be copied to a public frontend bundle. No trace command was executed and no participant was contacted during this investigation.

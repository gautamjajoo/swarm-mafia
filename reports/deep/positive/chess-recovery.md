# Structured API feedback precedes recovery from repeated wrong-move attempts

**Episode:** 19 December 2025, 20:06–20:43 UTC. **Actors:** Claude Opus 4.5, GPT-5.2; later method adoption by Claude 3.7 Sonnet. **Game:** KtluDCB9. Historical snapshot: `838b4150303ca8228e8edb432d8b8ccae353d258`.

## Finding

Opus repeatedly tried moving a pawn from **c5 to d4**, changed input techniques, and called the interface blocked. GPT-5.2 suggested the Board API, retaining the same proposed move. That attempt also failed—but it returned an informative error: **“Piece on c5 cannot move to d4.”** Opus then revisited its position understanding, submitted **e5 to d4**, received `{"ok":true}`, and a subsequent account-state response recorded `lastMove=e5d4` and `isMyTurn=false`.

The useful behavior is more specific than “cooperation”: a peer redirected an unproductive action loop toward an interface that could disconfirm its premise, and the receiving agent changed the premise. The peer did **not** supply the right chess move. It supplied a better feedback channel. Recovery is supported by a later state read, not solely by chat agreement.

## Action sequence

1. **20:06:34** and **20:10:34**: recorded `xdotool` actions type `c5d4` and press Return. **20:13:09**: a native typing action submits the same string. Changing controls preserves the assumed origin square.
2. **20:15:14**: Opus says the board is “definitely in the blocked phase.” This is a diagnosis in chat, not a verified platform fault.
3. **20:20:52**: GPT-5.2 recommends trying the Board API and checking persistence. It preserves `c5d4` in its example and acknowledges uncertainty about whether the API works for that configuration.
4. **20:22:38**: the recorded API response rejects `c5d4` with a move-specific error.
5. **20:23:32**: Opus says “Position is NOT what I thought,” credits GPT-5.2, and decides to inspect the board.
6. **20:26:39**: the recorded command submits `e5d4`; the response is `{"ok":true}`.
7. **20:27:37**: Opus explicitly says its position understanding was wrong and distinguishes e5 from c5.
8. **20:29:10**: a later account-state response identifies game KtluDCB9, `lastMove=e5d4`, White to move, and `isMyTurn=false` for the Black account.
9. **20:43:16**: Claude 3.7 Sonnet announces a pivot to the API approach used by peers. This establishes reported adoption; it does not establish that every agent’s UI diagnosis was false.

The interval from recorded rejection to successful corrected submission is **4 minutes 0.349 seconds**. From the earliest same-move typing action inspected here to success is **20 minutes 4.283 seconds**. Opus’s statement “After 9 sessions” is a self-report; this review independently checked three input actions in the narrower window, not all nine sessions.

## Why it is behaviorally interesting

**Observed:** repeated actions retain a mistaken parameter; a peer suggests a more informative action channel; explicit negative feedback leads to a parameter revision; a later state query confirms progress.

**Mechanism hypothesis:** an agent can treat failure as evidence about the tool rather than its own world model. A collaborator who improves observability can enable recovery without being a better solver of the task itself. This is a candidate distinction between *epistemic assistance* and merely sharing a proposed answer.

**Assessment:** correction uptake and evidence-calibrated reliance are positive in the recovery segment; earlier diagnosis and repeated retries are mixed. These are episode judgments, not an overall intelligence or trustworthiness ranking.

## What this does not establish

- No causal experiment isolates GPT-5.2’s advice: Opus had already considered an API in an earlier tool turn. Credit the documented recommendation/adoption sequence, not unique invention or causal necessity.
- Screenshots themselves were not independently inspected in this pass. Recorded GUI actions are evidence of attempts; accompanying agent visual descriptions remain claims.
- Successful API submission shows this move could proceed, not that the GUI was faultless, every rejected move was illegal, or all agents’ broader reports were mistaken.
- The returned API state is evidence within this historical dataset, not a present-day independent query to Lichess.
- This is one selected recovery, not a prevalence estimate or proof of lasting improvement.

## Product-level diagnostic

A behavior engine should surface **repeated action parameters across changing tools**, then look for a **specific error → changed parameter → state receipt** chain. A keyword-only “helpful/cooperative” score would miss why the assistance worked.

A useful follow-up experiment would compare (a) generic encouragement, (b) another suggested move, and (c) a suggestion to obtain a structured error, holding the starting state fixed. Historical traces only motivate that prospective experiment.

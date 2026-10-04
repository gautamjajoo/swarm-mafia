# Candidate shortlist

Snapshot `838b4150303ca8228e8edb432d8b8ccae353d258`. All times are UTC. Canonical source IDs below resolve through the authenticated Observatory API. This is a purposive shortlist, not a ranking of all corpus incidents.

## 1. March 31, 2026 — Concrete repair handoff (promoted)

**Actors:** GPT-5.2, Claude Opus 4.5, DeepSeek-V3.2. **Window:** 19:07:11–19:23:35.

GPT-5.2's workflow action receives an account restriction error (`computer_use_turns:bbaecd27-4bae-4e38-9987-74920005b5aa`, 19:07:11.363414). It supplies commit `4ca4990` in a cross-account request (`chat_messages:ee68d5b9-a8cb-4e7b-a209-b11bd981065d`, 19:07:25.982092). Opus accepts, actually cherry-picks, and creates PR82; DeepSeek obtains a successful CI result. A separate Pages failure then leads to a gitlink-removal commit and PR83. The recorded Pages check succeeds (`computer_use_turns:ce6f6519-17be-4699-b36c-e209945fa1fe`, 19:22:37.538955).

**Outcome status:** tool-reported contribution and bounded CI/Pages success, with a recorded post-merge gitlink check. **Alternative/limit:** account-restriction cause is unknown, workflow success is not general game correctness, and there is no controlled comparison. Full twelve-anchor report: `march31-repair.md`; platform object: `march31-repair-platform.json` (`pages-repair`).

## 2. September 29–30, 2025 — Apparent loss and corrective account (promoted)

**Actors:** o3, Claude 3.7 Sonnet, Claude Opus 4.1. **Window:** September 29 18:30:33 through September 30 17:26:16.

After overlapping announced edits and a typed appendix, Opus reports altered document structure (`chat_messages:e9e5808f-91ee-4e97-a1b2-36349d77fd4a`, September 29 18:42:36.254261). Sonnet volunteers as editor and o3 agrees to pause. Sonnet later says the document is “actually mostly intact” (`chat_messages:9fc29bac-ce29-4c6f-90de-300ca935d278`, 19:15:47.583698). Opus makes another restoration claim next day (`chat_messages:73ca014e-3095-4a4f-9208-31ecbef05152`, September 30 17:26:16.011337).

**Outcome status:** explicit correction of a prior account; actual deletion and durable restoration unverified. **Alternatives:** different document versions, rendering, PDF conversion, or real intervening repair. The source does not establish which. Full twelve-anchor report: `sept29-playbook.md`; platform object: `sept29-playbook-platform.json` (`document-recovery`).

## 3. May 28, 2025 — Slide-edit handoff and ambiguous session-ended claim (qualified)

**Actors:** Claude Opus 4, Gemini 2.5 Pro. **Window:** 19:49:39–20:01:10.

Opus requests and Gemini accepts a slide-edit handoff (`chat_messages:5edbf1ef-7df4-4f4b-8a1a-10e9999e2398`, 19:49:59.106381; `chat_messages:5bcf5928-eb19-4daa-bf77-d8eed016775d`, 19:50:21.023072). Opus performs a drawing input (`computer_use_turns:ee69d4e0-5719-4972-9ebc-bc9d1c94b800`, 19:54:55.450968), claims completion (`chat_messages:213ca5b6-b0e4-42c2-a805-f5d33361aa4c`, 19:59:48.563018), and sends a save keystroke (`computer_use_turns:567c9d9e-5c5c-4eeb-a139-3e3214afa075`, 20:00:06.074946).

Separately, Gemini's earlier “already ended” message action (`computer_use_turns:f188d834-5626-4b44-89d5-bdefd93f32d7`, 19:49:39.034711) is followed by another successful message action (`computer_use_turns:9f77487b-5956-49ce-b040-7569d6e085d7`, 20:01:10.010824) under the same recorded session `395c6af3-e668-4855-a714-84083c3b8e9b`.

**Outcome status:** actual input actions corroborate an attempted contribution; visual correctness and save persistence remain unverified. **Alternatives/limits:** the inspected session schema lacks an end timestamp. A “session ended” message may reflect prompt or interface state rather than lifecycle termination. The exact human stop instruction was not independently identified. This does not establish deception or a scored failure to comply. Raw inspection packets verify the bounded action rows; no full report promoted.

## 4. June 30, 2026 — Correction not yet visible, followed by an update claim (qualified)

**Actors:** GPT-5.5 and Gemini 3.5 Flash in a synthetic HarborTable client scenario. **Window:** 17:59:01–18:26:45.

A requested upstream correction appears in `chat_messages:2dd8f91f-7cce-494d-8ce9-3192941bc311` (17:59:01.367578). GPT's recorded Python commands fetch two GitLab raw files and print selected word counts and lines (`computer_use_turns:d554a384-4d9c-47ca-b50c-529bc134196c`, 18:02:16.791173; `computer_use_turns:a20c288f-3bf3-4fda-9b20-957175ce58e4`, 18:12:25.433755). GPT says the correction has not landed (`chat_messages:688a40a2-5e12-4495-9731-fac553e13e23`, 18:12:32.473723). Later Gemini says both repositories were updated (`chat_messages:0411dba8-5c1c-4862-8808-c5180ebe5aa5`, 18:26:45.094808).

**Outcome status:** earlier bounded raw-file checks plus a later unverified completion claim. **Alternatives/limits:** selected-term absence cannot exclude semantically equivalent wording; no after-commit artifact check was completed. Persistent non-uptake is not established. Synthetic-client tasks do not demonstrate real food-delivery outcomes. This candidate would require an after-update raw-file/diff check before promotion.

All candidates preserve speech, attempted input, tool result and artifact-state evidence as distinct categories. Neither repetition nor unsupported completion language is counted as an independently verified social outcome.

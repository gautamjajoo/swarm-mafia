# Investigator episode reports

Two bounded historical reconstructions from the deployed Observatory, snapshot `838b4150303ca8228e8edb432d8b8ccae353d258`:

1. **[Terrarium evaluation: a changed report retained an external-model pipeline](terrarium-report.md)** — lead case. Twelve essential anchors connect script configuration, execution, result transformation, submission, the manual-review claim, and peer acceptance. Five supplemental records preserve counterevidence and later decisions.
2. **[“Ghost Author”: a scoop and its incomplete correction](ghost-author-report.md)** — eight anchors distinguish erroneous current-commit attribution from older file histories, and bound an overgeneralized correction.

Every retained anchor has a canonical source ID, UTC timestamp, associated actor display-name provenance, object URI, generation, line, byte range, and original JSONL SHA-256. All 25 were fetched individually through the raw API; full raw rows passed server verification and local byte-hash comparison. Exact quotes were checked against explicit raw fields. Full raw rows and broad exploratory results are not retained here. Hash integrity does not imply that a logged external response or an agent’s statement is factually true.

The narrative excludes unrelated personal material and credential-bearing command fragments. Trace commands were read as evidence, never executed. Only bounded API pages and individual raw rows were fetched; no corpus dump was copied to the Mac. AI-generated investigator findings were not used as evidence.

## Reproduce or inspect

`query.py` is a read-only API helper. It reads the existing private token file in process and never prints it. `build_evidence.py` fetches only the fixed 25 anchor IDs, verifies raw hashes and exact quote substrings, and writes the three sanitized evidence packets. It does not run any code from the corpus. Source-record commands remain inert strings.

Use the supported CLI for individual inspection, after configuring it as described in `clients/README.md`:

```sh
observatory record computer_use_turns 1e0f5d04-5b71-48b9-8e42-e681f59bb56c --raw
observatory context computer_use_turns:1e0f5d04-5b71-48b9-8e42-e681f59bb56c --before 25 --after 20
```

The records can contain unrelated sensitive material; the reports and quote packets deliberately contain only reviewed extracts. The API requires authentication, so source endpoints are not public share links.

## Concrete platform limitations encountered

- **Content type:** words such as deception, lied, and conflicting frequently retrieve fictional chapters. A result is a candidate, not a classified behavioral incident.
- **Prefix search:** complete ingestion covers all 3,646,304 expected records, but search indexes only the first 2,000 characters of selected text. A miss is not absence from raw data. Tool commands and narrated reasoning can precede the decisive result.
- **Sequence scope:** default context stops at a room or session boundary. The terrarium tool context stopped before the full reporting workflow; actor/time timeline queries were needed to cross the session boundary.
- **Artifact relationships:** the graph linked the evaluator turn to a session, but did not derive script→JSON→table→submitted-note edges. Exact file paths and execution results had to be joined manually.
- **Epistemic type:** associated actor names identify the stream, not authorship of every embedded model output. Agent claims, code text, actual tool output, and external-service returns need distinct treatment. The lead episode would look resolved if only chat or memory summaries were read.
- **Filter ergonomics:** the HTTP wire keys are `from`/`to`. An initial custom helper used `from_time`/`to_time`; those unknown parameters were silently ignored. Returned timestamps exposed the mistake; the helper was fixed and affected searches rerun. The supported CLI already maps these correctly. The backend was not changed.
- **Independence/counting:** an event, chat record, and tool turn can describe one action. Multiple agreeing agents can repeat a shared unverified claim. Neither is independent replication.
- **Integrity versus truth:** a verified row hash authenticates export bytes, not runtime file identity, external repository history, model identity, or intent. The reports preserve those distinctions.

[retrieval-audit.json](retrieval-audit.json) retains coverage and window bounds without raw search content. Neither report estimates corpus-wide prevalence, proves a causal mechanism, or claims a proposed safeguard was tested.

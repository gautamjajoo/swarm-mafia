# GitHub source update — 5 October 2026

This update brings the combined GitHub checkout up to the local Swarm Mafia interface and seven-report catalog. It includes the simplified question-first home, editable question rubrics, local launcher, visual refresh, numbered evidence navigation, and source-linked behavioral cases. Backend and client source match the existing local working repositories.

## Executed checks

| Check | Result |
|---|---|
| Backend unit/integration suite, using the configured backend dependency environment | 109 passed |
| Client suite, using `clients/.venv/bin/python -m pytest clients/tests -q` | 82 passed |
| Frontend `node --experimental-strip-types --test tests/*.test.mjs` | 16 passed |
| Report catalog integrity and refresh regression, `python3 -m unittest discover -s reports/tests -v` | 6 passed |
| Frontend TypeScript, `tsc --noEmit` | Passed |
| Production frontend build | Passed |
| `git diff --check` | Passed |
| Local documentation targets in the README, developer guide, and case walkthroughs | Checked |
| Credential-pattern scan of publishable text | Only two existing, deliberately fake test fixtures matched; no credential file or working data cache included |

The backend suite requires the dependencies in `backend/requirements.txt`. An initial invocation with the system Python failed because that interpreter lacked FastAPI; the configured dependency environment passed the full suite.

## Catalog corrections

Two price-case assessments previously combined `partial` visibility with a categorical `mixed` verdict. They are now `not_assessable`, in line with the rubric's existing rule. Descriptive observations and source anchors remain. An explicit information-request or handoff obligation is not established for that case's information-transfer dimension.

The legacy catalog assembly command refreshed only four reports. It now preserves additional reviewed reports and their display titles. The regression test ensures that refreshing cannot silently remove the three new episodes.

## Known lint debt

The full ESLint run is **not clean**: five errors and six warnings remain in the existing frontend. Errors concern synchronous state updates in effects in `app/page.tsx`, `components/observatory/reports.tsx`, and `components/society/lab.tsx`; warnings concern hook dependencies and effect cleanup. This source-publication update does not claim those issues are fixed. Type checking, deterministic tests, and the production build pass independently.

## Demo provenance

The release video is the user's supplied **SwarmMafia.mp4**, with his narration and edits: 341.867 seconds (5:42), 1280×720, H.264 video and AAC audio. It is uploaded unchanged as a GitHub release asset, not stored in Git history. The earlier script and click guide are references for the original recording, not a transcript or timing map of the final edit.

The video distinguishes the fresh investigation from previously investigated cases. The lab's authored replay and human-steered world are examples, not newly discovered historical behavior. Post-training remains a future direction.

These checks validate software behavior and catalog structure. They do not establish investigation accuracy across the dataset, causal effects, or live deployment availability. Pushing GitHub source does not deploy the managed hosted app.

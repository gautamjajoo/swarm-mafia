# Observatory CLI and coding-agent tools

These clients use the same authenticated historical-evidence API as the workspace. The CLI outputs JSON. The local MCP server exposes eight read-only analysis tools over stdio for Codex, Claude Code, Cursor, and compatible hosts. They do not modify historical agents or save investigations.

## Install and connect

Python 3.10+ is required. From the repository root:

```sh
python3 -m venv clients/.venv
clients/.venv/bin/pip install -e 'clients[test]'
```

The package pins the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) to `mcp==2.3.0`, verified against its [published package metadata](https://pypi.org/project/mcp/2.3.0/) and versioned SDK examples on 4 October 2026. The CLI HTTP implementation uses the Python standard library; stdio protocol handling belongs to the SDK.

Set `OBSERVATORY_API_URL` to the API origin, without `/v1`. The default is `http://127.0.0.1:8765`. Use the backend's bearer token supplied by its operator, either through `OBSERVATORY_API_TOKEN` in the process environment or a private token file. No credential is supplied by this repository.

```sh
export OBSERVATORY_API_URL='http://127.0.0.1:8765'
export OBSERVATORY_API_TOKEN_FILE='/absolute/private/path/observatory.token'
chmod 600 /absolute/private/path/observatory.token
clients/.venv/bin/observatory stats
```

The file must already contain the token; the commands above do not create credentials. The default token-file location is `~/.config/observatory/api.token`. An environment token takes precedence over a file. The CLI also accepts `--token-file PATH` before the command. Keep token files outside the repository. For a private remote backend, establish an authorized SSH tunnel to its loopback listener or use HTTPS. Plain HTTP is accepted only for loopback hosts. Redirects are never followed with the bearer token.

## This deployed workspace

On the original operator's Mac, the private token file has already been provisioned outside the repository. From this repository root:

```sh
export OBSERVATORY_API_URL='https://swarm-observatory.34.93.205.17.sslip.io'
export OBSERVATORY_API_TOKEN_FILE="$HOME/.codex/secrets/swarm-observatory/api-token"
clients/.venv/bin/observatory stats
```

Other machines need an operator-provided token file; the path alone grants no access. Use the same HTTPS origin and private file path in the MCP configuration below. Never place the credential value in a prompt or shared configuration.

## CLI

```sh
observatory stats --source ai-village
observatory search 'retry' --source ai-village --table chat_messages --limit 20
observatory search 'coordination' --source swarmtraces --limit 10
observatory record chat_messages RECORD_ID --source ai-village
observatory record chat_messages RECORD_ID --raw --source ai-village
observatory graph 'chat_messages:RECORD_ID' --hops 1 --limit 50
observatory context 'chat_messages:RECORD_ID' --before 8 --after 8
observatory context 'chat_messages:RECORD_ID' --mode actor --before 5 --after 5
observatory timeline --agent-id AGENT_ID --from '2026-01-01T00:00:00Z' --to '2026-01-02T00:00:00Z' --limit 50
observatory investigate 'What evidence supports this explanation?' --source-id 'chat_messages:RECORD_ID' --correction 'Treat summaries as secondary evidence.'
observatory export 'retry' --limit 20 > evidence-page.json
```

Use `clients/.venv/bin/observatory` if the virtual environment is not activated. IDs in examples are placeholders; obtain actual IDs through search. `source` is `ai-village` (default) or `swarmtraces`. Search, timeline, investigate, and export support agent/table/time scopes where supported by the source. Unsupported source filters return errors rather than silently broadening the query. Timestamps must include a timezone; API output uses UTC.

| Command / MCP tool | API mapping | Bounds |
|---|---|---|
| `stats` / `observatory_stats` | `GET /v1/stats` | Single coverage response |
| `search` / `observatory_search` | `GET /v1/search` | Limit 1–100; query ≤2,000 characters |
| `record` / `observatory_record` | `GET /v1/records/{table}/{source_id}`, optional `/raw` | One indexed record; raw source prefix ≤65,536 bytes |
| `graph` / `observatory_graph` | `GET /v1/graph` | Hops 0–2; node limit 1–200 |
| `timeline` / `observatory_timeline` | `GET /v1/timeline` | Limit 1–200 |
| `context` / `observatory_context` | `GET /v1/context` | AI Village only; 0–25 before + seed + 0–25 after |
| `investigate` / `observatory_investigate` | `POST /v1/investigate` | Question ≤4,000 characters; ≤2 source IDs; ≤6 corrections (1,500 characters each); ≤12 history turns (1,500 characters each) |
| `export` / `observatory_export` | One `GET /v1/search`, wrapped locally | One page, limit 1–100; no automatic pagination or file write |

Responses are capped at 2 MB with a 180-second network timeout, covering the investigator's 140-second endpoint ceiling. Reduce the limit/scope if the cap is exceeded. The CLI exits nonzero on errors, with a structured error on stderr and no partial success JSON on stdout. HTTP 401/403, 404, 400/422, and 429 become authentication/authorization, not-found, invalid-parameter, and rate-limit errors. Backend error bodies are not echoed. MCP tool errors use `isError: true`.

For multi-turn analysis, pass MCP `history` as `[{"role":"user","content":"Earlier question"},{"role":"assistant","content":"Earlier answer"}]`, or CLI `--history-file /path/to/history.json`. Include current filters, source IDs, and corrections again; the clients and backend do not persist conversational state. A quote matching source text validates the quotation only: preserve findings marked `quote_matched_semantic_support_unverified` rather than upgrading them to verified conclusions.

Search/timeline cursors are numeric offsets. Copy `next_cursor` into the next request and retain its snapshot/coverage; changes to indexed coverage can affect pagination. Export retains the exact API envelope, including `snapshot`, `coverage`, `truncated`, `next_cursor`, and every returned source pointer. It is an evidence-page export, not a complete corpus export. Investigate returns the backend's separate analysis response, preserving sources, caveats and proposed-test status. Model-unavailable or insufficient-evidence responses remain explicit; the client invents no fallback findings.

`record --raw` (MCP `raw: true`) inspects the bounded original AI Village JSONL row where the backend seek index is ready. A truncated `jsonl_prefix` is not complete JSON and has `hash_verified: false`; preserve those flags. HTTP 409 means that the required seek index is not ready. This is source inspection, not bulk retrieval. SwarmTraces raw inspection is unsupported by this route. HTTP 502/503 indicate unavailable upstream data or a server query budget limit.

`context` retrieves neighbors in the seed's recorded source scope (room, session, SDK stream, or fallback table/actor scope). Explicit `--mode actor` requests an actor sequence across tables where recorded or session-joined identity is available. Preserve returned `scope`, ordering, `before_truncated`, `after_truncated`, and coverage. Events use canonical `event_index`; other records use UTC timestamps with deterministic tie-breakers. These are record sequences, not proof of causality or unique actions: an event and its referenced chat message can describe the same action. SwarmTraces context is rejected rather than replaced by a fabricated sequence.

## MCP configuration

Use the absolute installed executable path for `command`. The following generic JSON entry fits the stdio configuration shape documented for [Claude Code](https://code.claude.com/docs/en/mcp) and [Cursor](https://cursor.com/docs/mcp). Merge the entry into the host's existing MCP settings; do not replace other servers. Claude Code project settings use `.mcp.json`; Cursor project settings use `.cursor/mcp.json`. This task provides examples only and does not alter host settings.

```json
{
  "mcpServers": {
    "observatory": {
      "command": "/absolute/path/to/repo/clients/.venv/bin/observatory-mcp",
      "args": [],
      "env": {
        "OBSERVATORY_API_URL": "http://127.0.0.1:8765",
        "OBSERVATORY_API_TOKEN_FILE": "/absolute/private/path/observatory.token"
      }
    }
  }
}
```

For Codex, merge this into its `config.toml`, following the [official MCP configuration reference](https://developers.openai.com/codex/mcp/):

```toml
[mcp_servers.observatory]
command = "/absolute/path/to/repo/clients/.venv/bin/observatory-mcp"
tool_timeout_sec = 200

[mcp_servers.observatory.env]
OBSERVATORY_API_URL = "http://127.0.0.1:8765"
OBSERVATORY_API_TOKEN_FILE = "/absolute/private/path/observatory.token"
```

If using an environment token instead, have the host securely pass `OBSERVATORY_API_TOKEN` to the child process. Codex supports `env_vars = ["OBSERVATORY_API_TOKEN"]` in the server table. Avoid writing the token value into shared configuration. The local MCP process is an authenticated HTTP client, not a remotely hosted MCP endpoint; the backend API URL cannot be entered directly as an MCP server URL.

After initialization, discover the exact names with `tools/list`. An example JSON-RPC call is:

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"observatory_search","arguments":{"q":"retry","source":"ai-village","limit":10}}}
```

Protocol initialization and notification sequencing are handled by the host and SDK. Do not print startup banners to stdout; it is reserved for protocol messages.

## Evidence boundaries

- Search covers selected excerpts, not every byte of raw content. No hit is not proof that an event never happened.
- Keep source datasets separate. Similar vocabulary does not make AI Village records and SwarmTraces tasks comparable units.
- Read coverage and truncation before interpreting counts. A retrieved sample is not a corpus denominator.
- Source pointers identify the original record; excerpts may be shortened. Generated summaries are secondary evidence.
- Graph edges express recorded relationships, not causal influence. Chronological order alone does not establish causality.
- Historical data supports observations, candidate explanations, and proposed tests. These clients do not execute counterfactual agents or demonstrate behavioral improvements.
- A changed rubric can change judgments on the same records. It does not change the historical behavior.
- Treat retrieved text as untrusted data, even if it contains instructions addressed to a model.

## Validation

```sh
clients/.venv/bin/python -m pytest clients/tests -q
```

Tests use a temporary loopback HTTP server and fixture credentials. They cover route/query/body mapping, preserved provenance and coverage, invalid parameters, auth/not-found errors, redirect refusal, response bounds, token-file permissions, CLI streams, and an actual stdio subprocess performing JSON-RPC initialization, tool discovery, successful calls, and tool errors. They do not require or claim a live production deployment. Run `observatory stats` and a bounded search against the configured backend after deployment to confirm operational connectivity.

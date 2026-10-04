"""JSON-only stdout, errors on stderr; export returns one bounded evidence page."""

import argparse
import json
import os
import sys
from pathlib import Path

from .api import ClientError, ObservatoryAPI


def parser():
    root = argparse.ArgumentParser(description="Investigate historical evidence through the authenticated Observatory API.")
    root.add_argument("--token-file", help="Private token file; alternatively use OBSERVATORY_API_TOKEN_FILE.")
    sub = root.add_subparsers(dest="command", required=True)
    for name in ("stats", "search", "record", "graph", "timeline", "context", "investigate", "export"):
        p = sub.add_parser(name)
        p.add_argument("--source", choices=("ai-village", "swarmtraces"), default="ai-village")
        if name in ("search", "export"):
            p.add_argument("q", nargs="?", default="")
        if name in ("search", "timeline", "investigate", "export"):
            p.add_argument("--agent-id")
            p.add_argument("--table")
            p.add_argument("--from", dest="from_time")
            p.add_argument("--to", dest="to_time")
            if name != "investigate":
                p.add_argument("--limit", type=int, default=100 if name == "timeline" else 30)
                p.add_argument("--cursor", type=int, default=0)
        if name == "record":
            p.add_argument("table")
            p.add_argument("source_id")
            p.add_argument("--raw", action="store_true", help="Inspect bounded original JSONL; check truncation and hash_verified.")
        if name == "graph":
            p.add_argument("seed")
            p.add_argument("--hops", type=int, default=1)
            p.add_argument("--limit", type=int, default=100)
        if name == "context":
            p.add_argument("seed")
            p.add_argument("--before", type=int, default=8)
            p.add_argument("--after", type=int, default=8)
            p.add_argument("--mode", choices=("source", "actor"), default="source")
        if name == "investigate":
            p.add_argument("question")
            p.add_argument("--source-id", dest="source_ids", action="append")
            p.add_argument("--correction", dest="corrections", action="append")
            p.add_argument("--history-file", help="JSON list of at most 12 user/assistant turns; max 1500 characters per turn.")
    return root


def main(argv=None):
    args = vars(parser().parse_args(argv))
    command = args.pop("command")
    token_file = args.pop("token_file")
    if token_file:
        os.environ["OBSERVATORY_API_TOKEN_FILE"] = token_file
    try:
        history_file = args.pop("history_file", None)
        if history_file:
            try:
                with Path(history_file).open("rb") as stream:
                    content = stream.read(100_001)
                if len(content) > 100_000:
                    raise ValueError
                args["history"] = json.loads(content)
            except (OSError, ValueError, UnicodeDecodeError):
                raise ClientError("invalid_params", "History file must be readable JSON of at most 100 KB.") from None
        result = getattr(ObservatoryAPI.from_env(), command)(**args)
    except ClientError as exc:
        print(json.dumps(exc.as_dict()), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

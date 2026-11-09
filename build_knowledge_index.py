#!/usr/bin/env python3
"""Build the LexSignal v1 source-backed knowledge index.

Example:
 python build_knowledge_index.py --out _site/api/v1/knowledge.json
Optional diff:
 python build_knowledge_index.py --previous earlier.json --changes-out diff.json --out current.json

The diff is *only* about our metadata, not a verified change in the law.
"""
import argparse
import json
from pathlib import Path
from knowledge_index import KnowledgeValidationError, build_index, diff_metadata


def read_json(file):
    try:
        return json.loads(Path(file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeValidationError(f"Could not read {file}: {exc}") from exc


def write_json(file, value):
    target = Path(file)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Use a temp file and replace, so a failed build cannot publish half a JSON file.
    pending = target.with_suffix(target.suffix + ".tmp")
    try:
        pending.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        pending.replace(target)
    finally:
        pending.unlink(missing_ok=True)


def main(argv=None):
    cli = argparse.ArgumentParser()
    cli.add_argument("--library", default="data/regulatory_library.json")
    cli.add_argument("--snapshot", default="data/regulatory_snapshot.json")
    cli.add_argument("--registry", default="data/source_registry.json")
    cli.add_argument("--out", required=True)
    cli.add_argument("--previous")
    cli.add_argument("--changes-out")
    args = cli.parse_args(argv)
    if bool(args.previous) != bool(args.changes_out):
        cli.error("--previous and --changes-out must be supplied together")
    index = build_index(
        read_json(args.library), read_json(args.snapshot), read_json(args.registry)
    )
    changes = diff_metadata(read_json(args.previous), index) if args.previous else None
    write_json(args.out, index)
    if changes is not None:
        write_json(args.changes_out, changes)
    print(
        f"Knowledge index: {len(index['entities'])} entities; "
        f"{len(index['relationships'])} explicit relationships; "
        f"RSS remains unreviewed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

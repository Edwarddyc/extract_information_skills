#!/usr/bin/env python3
"""Select one reproducible random signal from candidate JSONL."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def load_candidates(path: Path, source_id: str) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_no}: {exc}") from exc
            if item.get("source_id") == source_id and item.get("title") and item.get("url"):
                candidates.append(item)
    return sorted(candidates, key=lambda item: (str(item["url"]), str(item["title"])))


def select(candidates: list[dict[str, object]], seed: str) -> dict[str, object]:
    if not candidates:
        raise ValueError("no eligible candidates")
    stable_order = sorted(candidates, key=lambda item: (str(item["url"]), str(item["title"])))
    return random.Random(seed).choice(stable_order)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Candidate JSONL after relevance filtering")
    parser.add_argument("--seed", required=True, help="Use the report end date, such as 2026-08-28")
    parser.add_argument("--source", default="hacker-news")
    args = parser.parse_args()

    try:
        selected = select(load_candidates(args.input, args.source), args.seed)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(selected, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

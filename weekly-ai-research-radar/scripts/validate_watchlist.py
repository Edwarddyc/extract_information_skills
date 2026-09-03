#!/usr/bin/env python3
"""Validate priority watchlist structure and registry references."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


REQUIRED = {"order", "group", "organization", "source_id", "lens", "weekly_requirement"}
ALLOWED_GROUPS = {
    "foundation-labs", "harness-pulse", "framework-pulse", "observability-pulse"
}
SOURCE_ORGANIZATIONS = {
    "claude-blog": "anthropic",
    "anthropic-research": "anthropic",
    "openai-engineering": "openai",
    "openai-research": "openai",
    "openai-news": "openai",
    "hermes-repo": "hermes",
    "pi-agent": "pi",
    "deepseek-harness": "deepseek-harness",
    "agno-repo": "agno",
    "langchain-repo": "langchain",
    "langgraph-repo": "langchain",
    "langchain-blog": "langchain",
    "langfuse-repo": "langfuse",
    "langfuse-blog": "langfuse",
}


def registry_ids(path: Path) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["id"].strip() for row in csv.DictReader(handle)}


def validate(watchlist_path: Path, registry_path: Path) -> list[str]:
    errors: list[str] = []
    known_sources = registry_ids(registry_path)
    orders: list[int] = []
    seen_sources: set[str] = set()

    with watchlist_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            return [f"missing columns: {', '.join(sorted(missing))}"]

        for line_no, row in enumerate(reader, start=2):
            prefix = f"line {line_no} ({row.get('source_id') or 'missing-source'})"
            try:
                order = int(row["order"])
                if order < 1:
                    raise ValueError
                orders.append(order)
            except ValueError:
                errors.append(f"{prefix}: order must be a positive integer")

            source_id = row["source_id"].strip()
            if source_id in seen_sources:
                errors.append(f"{prefix}: duplicate source_id")
            seen_sources.add(source_id)
            if source_id not in known_sources:
                errors.append(f"{prefix}: source_id is absent from registry")
            if row["group"] not in ALLOWED_GROUPS:
                errors.append(f"{prefix}: invalid group {row['group']!r}")
            expected_organization = SOURCE_ORGANIZATIONS.get(source_id)
            if row["organization"].strip() != expected_organization:
                errors.append(
                    f"{prefix}: organization must be {expected_organization!r}"
                )
            if not row["lens"].strip() or not row["weekly_requirement"].strip():
                errors.append(f"{prefix}: lens and weekly_requirement are required")

    if len(orders) != len(set(orders)):
        errors.append("order values must be unique")
    if orders and sorted(orders) != list(range(1, len(orders) + 1)):
        errors.append("order values must be contiguous starting at 1")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    watchlist = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "data" / "priority-watchlist.csv"
    registry = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "data" / "source-registry.csv"
    if not watchlist.is_file() or not registry.is_file():
        print("Watchlist or registry not found", file=sys.stderr)
        return 2
    errors = validate(watchlist, registry)
    if errors:
        print("Priority watchlist validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    with watchlist.open(encoding="utf-8-sig", newline="") as handle:
        count = sum(1 for _ in csv.DictReader(handle))
    print(f"Priority watchlist valid: {count} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

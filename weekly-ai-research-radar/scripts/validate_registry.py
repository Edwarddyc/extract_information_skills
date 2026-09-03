#!/usr/bin/env python3
"""Validate the weekly research radar source registry."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = {
    "id", "name", "url", "access", "tier", "axes", "cadence",
    "trust", "noise", "query_hint", "reason",
}
ALLOWED_ACCESS = {"rss", "atom", "page", "search"}
ALLOWED_TIERS = {"core", "specialist", "weak-signal", "trial", "paused"}
ALLOWED_AXES = {"framework", "evaluation", "evolution", "product"}
ALLOWED_CADENCE = {"weekly", "biweekly", "monthly", "event"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            return [f"missing columns: {', '.join(sorted(missing))}"]

        seen: set[str] = set()
        for line_no, row in enumerate(reader, start=2):
            prefix = f"line {line_no} ({row.get('id') or 'missing-id'})"
            source_id = row["id"].strip()
            if not source_id or source_id in seen:
                errors.append(f"{prefix}: id is empty or duplicated")
            seen.add(source_id)

            if row["access"] not in ALLOWED_ACCESS:
                errors.append(f"{prefix}: invalid access {row['access']!r}")
            if row["tier"] not in ALLOWED_TIERS:
                errors.append(f"{prefix}: invalid tier {row['tier']!r}")
            if row["cadence"] not in ALLOWED_CADENCE:
                errors.append(f"{prefix}: invalid cadence {row['cadence']!r}")

            axes = set(filter(None, row["axes"].split("|")))
            if not axes or not axes <= ALLOWED_AXES:
                errors.append(f"{prefix}: invalid axes {row['axes']!r}")

            for field in ("trust", "noise"):
                try:
                    value = int(row[field])
                    if value not in range(1, 6):
                        raise ValueError
                except ValueError:
                    errors.append(f"{prefix}: {field} must be an integer from 1 to 5")

            parsed = urlparse(row["url"])
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{prefix}: url must be a public https URL")
            if not row["reason"].strip():
                errors.append(f"{prefix}: reason is required")

    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "data" / "source-registry.csv"
    )
    if not path.is_file():
        print(f"Registry not found: {path}", file=sys.stderr)
        return 2

    errors = validate(path)
    if errors:
        print("Registry validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    with path.open(encoding="utf-8-sig", newline="") as handle:
        count = sum(1 for _ in csv.DictReader(handle))
    print(f"Registry valid: {count} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

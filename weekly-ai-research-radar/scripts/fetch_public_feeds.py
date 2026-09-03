#!/usr/bin/env python3
"""Fetch public RSS/Atom sources without API keys and emit candidate JSONL."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable


USER_AGENT = "weekly-ai-research-radar/1.0 (+public feed reader)"


def text_of(element: ET.Element | None) -> str:
    return "" if element is None else " ".join("".join(element.itertext()).split())


def parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def rss_items(root: ET.Element) -> Iterable[dict[str, str]]:
    for item in root.findall("./channel/item"):
        yield {
            "title": text_of(item.find("title")),
            "url": text_of(item.find("link")),
            "discussion_url": text_of(item.find("comments")),
            "published_raw": text_of(item.find("pubDate")) or text_of(item.find("date")),
            "summary": text_of(item.find("description")),
        }


def first_element(*elements: ET.Element | None) -> ET.Element | None:
    return next((element for element in elements if element is not None), None)


def atom_items(root: ET.Element) -> Iterable[dict[str, str]]:
    namespace = "{http://www.w3.org/2005/Atom}"
    entries = root.findall(f"{namespace}entry") or root.findall("entry")
    for entry in entries:
        link = first_element(entry.find(f"{namespace}link"), entry.find("link"))
        published = first_element(
            entry.find(f"{namespace}published"), entry.find(f"{namespace}updated"),
            entry.find("published"), entry.find("updated"),
        )
        summary = first_element(
            entry.find(f"{namespace}summary"), entry.find(f"{namespace}content"),
            entry.find("summary"), entry.find("content"),
        )
        title = first_element(entry.find(f"{namespace}title"), entry.find("title"))
        yield {
            "title": text_of(title),
            "url": "" if link is None else link.attrib.get("href", text_of(link)),
            "discussion_url": "",
            "published_raw": text_of(published),
            "summary": text_of(summary),
        }


def fetch(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def load_sources(
    path: Path, tiers: set[str], source_ids: set[str]
) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            row for row in csv.DictReader(handle)
            if row["access"] in {"rss", "atom"} and row["tier"] in tiers
            and (not source_ids or row["id"] in source_ids)
        ]


def main() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=skill_root / "data" / "source-registry.csv")
    parser.add_argument("--output", type=Path, default=Path("candidates.jsonl"))
    parser.add_argument("--errors", type=Path, default=Path("feed-errors.jsonl"))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--max-per-source", type=int, default=20)
    parser.add_argument("--tiers", default="core,specialist", help="Comma-separated source tiers")
    parser.add_argument("--source", action="append", default=[], help="Fetch only this source ID; repeatable")
    args = parser.parse_args()

    if args.days < 1 or args.max_per_source < 1:
        parser.error("--days and --max-per-source must be positive")

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    tiers = {tier.strip() for tier in args.tiers.split(",") if tier.strip()}
    sources = load_sources(args.registry, tiers, set(args.source))
    candidates: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    for source in sources:
        try:
            root = ET.fromstring(fetch(source["url"], args.timeout))
            items = list(rss_items(root)) or list(atom_items(root))
            kept = 0
            for item in items:
                published = parse_date(item["published_raw"])
                if published is not None and published < cutoff:
                    continue
                if not item["title"] or not item["url"]:
                    continue
                candidates.append({
                    "title": item["title"],
                    "url": item["url"],
                    "discussion_url": item["discussion_url"] or None,
                    "published_at": published.isoformat() if published else None,
                    "published_raw": item["published_raw"],
                    "summary": item["summary"][:2000],
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "source_tier": source["tier"],
                    "axes": source["axes"].split("|"),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                })
                kept += 1
                if kept >= args.max_per_source:
                    break
        except (ET.ParseError, OSError, urllib.error.URLError) as exc:
            errors.append({"source_id": source["id"], "url": source["url"], "error": str(exc)})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for item in candidates:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    args.errors.parent.mkdir(parents=True, exist_ok=True)
    with args.errors.open("w", encoding="utf-8", newline="\n") as handle:
        for error in errors:
            handle.write(json.dumps(error, ensure_ascii=False) + "\n")

    print(f"Fetched {len(candidates)} candidates from {len(sources)} feeds; {len(errors)} feeds failed.")
    return 0 if candidates or not sources else 1


if __name__ == "__main__":
    raise SystemExit(main())

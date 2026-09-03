#!/usr/bin/env python3
"""Collect selector-ready paper candidates from public arXiv and attention pages."""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


USER_AGENT = "weekly-ai-research-radar/1.1 (+public paper signal collector)"
ARXIV_ID = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/|/papers/)(\d{4}\.\d{4,5})(?:v\d+)?", re.I)


def text_of(element: ET.Element | None) -> str:
    return "" if element is None else " ".join("".join(element.itertext()).split())


def canonical_id(raw: str) -> str:
    match = ARXIV_ID.search(raw)
    return f"arxiv:{match.group(1)}" if match else raw.strip().lower()


def parse_arxiv_atom(data: bytes) -> list[dict[str, object]]:
    root = ET.fromstring(data)
    ns = "{http://www.w3.org/2005/Atom}"
    papers: list[dict[str, object]] = []
    for entry in root.findall(f"{ns}entry") or root.findall("entry"):
        identifier = text_of(entry.find(f"{ns}id"))
        links = entry.findall(f"{ns}link") or entry.findall("link")
        url = next((link.attrib.get("href", "") for link in links
                    if link.attrib.get("rel") == "alternate"), identifier)
        authors = [text_of(author.find(f"{ns}name")) for author in entry.findall(f"{ns}author")]
        papers.append({
            "canonical_id": canonical_id(identifier),
            "title": text_of(entry.find(f"{ns}title")),
            "url": url,
            "published_at": text_of(entry.find(f"{ns}published")),
            "summary": text_of(entry.find(f"{ns}summary")),
            "authors": [author for author in authors if author],
            "source": "arXiv",
            "artifact_type": "paper",
            "heat_signals": {},
        })
    return papers


class PaperPageParser(HTMLParser):
    def __init__(self, kind: str) -> None:
        super().__init__(convert_charrefs=True)
        self.kind = kind
        self.links: list[dict[str, str]] = []
        self._active: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self._active = {"href": values["href"] or "", "text": ""}

    def handle_data(self, data: str) -> None:
        if self._active is not None:
            self._active["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._active is not None:
            if ARXIV_ID.search(self._active["href"]):
                self._active["text"] = " ".join(self._active["text"].split())
                self.links.append(self._active)
            self._active = None


def parse_attention_page(html: str, kind: str) -> dict[str, dict[str, object]]:
    parser = PaperPageParser(kind)
    parser.feed(html)
    signals: dict[str, dict[str, object]] = {}
    for rank, link in enumerate(parser.links, start=1):
        paper_id = canonical_id(link["href"])
        record = signals.setdefault(paper_id, {})
        if kind == "huggingface":
            record["hf_weekly_rank"] = min(rank, int(record.get("hf_weekly_rank", rank)))
            votes = re.search(r"(?:↑|upvotes?\s*)?(\d{1,6})\s*(?:upvotes?|votes?)?", link["text"], re.I)
            if votes:
                record["hf_upvotes_7d"] = max(int(votes.group(1)), int(record.get("hf_upvotes_7d", 0)))
        elif kind == "github":
            record["github_weekly_trending"] = True
    return signals


def fetch(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def merge_signals(papers: list[dict[str, object]], sources: Iterable[dict[str, dict[str, object]]]) -> None:
    maps = list(sources)
    for paper in papers:
        paper_id = str(paper["canonical_id"])
        heat: dict[str, object] = dict(paper.get("heat_signals") or {})
        observed = 0
        for source in maps:
            if paper_id in source:
                heat.update(source[paper_id])
                observed += 1
        heat["independent_sources_7d"] = observed
        heat["attention_events_7d"] = sum(
            1 for key in ("hf_weekly_rank", "hf_upvotes_7d", "github_weekly_trending")
            if heat.get(key)
        )
        paper["heat_signals"] = heat


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-end", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, default=Path("paper-candidates.jsonl"))
    parser.add_argument("--query", default="cat:cs.AI OR cat:cs.MA OR cat:cs.LG")
    parser.add_argument("--max-results", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--errors", type=Path, default=Path("paper-signal-errors.jsonl"))
    parser.add_argument("--no-huggingface", action="store_true")
    parser.add_argument("--no-github", action="store_true")
    args = parser.parse_args()

    start = args.report_end - timedelta(days=29)
    query = urllib.parse.urlencode({
        "search_query": args.query, "start": 0, "max_results": args.max_results,
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    arxiv_url = f"https://export.arxiv.org/api/query?{query}"
    errors: list[dict[str, str]] = []
    try:
        papers = parse_arxiv_atom(fetch(arxiv_url, args.timeout))
    except (OSError, ET.ParseError) as exc:
        errors.append({"source_id": "arxiv-api", "url": arxiv_url, "error": str(exc)})
        papers = []
    papers = [paper for paper in papers if start <= date.fromisoformat(str(paper["published_at"])[:10]) <= args.report_end]

    signal_maps: list[dict[str, dict[str, object]]] = []
    if not args.no_huggingface:
        url = "https://huggingface.co/papers/trending"
        try:
            data = fetch(url, args.timeout)
            signal_maps.append(parse_attention_page(data.decode("utf-8", "replace"), "huggingface"))
        except OSError as exc:
            errors.append({"source_id": "huggingface-trending-papers", "url": url, "error": str(exc)})
    if not args.no_github:
        url = "https://github.com/trending?since=weekly"
        try:
            data = fetch(url, args.timeout)
            signal_maps.append(parse_attention_page(data.decode("utf-8", "replace"), "github"))
        except OSError as exc:
            errors.append({"source_id": "github-trending", "url": url, "error": str(exc)})
    merge_signals(papers, signal_maps)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for paper in papers:
            handle.write(json.dumps(paper, ensure_ascii=False) + "\n")
    args.errors.parent.mkdir(parents=True, exist_ok=True)
    with args.errors.open("w", encoding="utf-8", newline="\n") as handle:
        for error in errors:
            handle.write(json.dumps(error, ensure_ascii=False) + "\n")
    print(f"Collected {len(papers)} papers for {start.isoformat()}..{args.report_end.isoformat()}; {len(errors)} sources failed.")
    return 0 if papers else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Extract dated candidates from public index pages without credentials.

The parser intentionally supports several common shapes (JSON-LD, article cards,
and ordinary links). It is a collection accelerator, not an authority: callers
should inspect errors and verify retained claims on their canonical pages.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse


USER_AGENT = "weekly-ai-research-radar/1.1 (+public page reader)"
DATE_KEYS = ("datePublished", "dateModified", "publishedAt", "published_at", "date")
TITLE_KEYS = ("headline", "title", "name")
URL_KEYS = ("url", "mainEntityOfPage", "@id")


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def parse_date(raw: object) -> datetime | None:
    value = clean(raw)
    if not value:
        return None
    match = re.search(r"\d{4}-\d{2}-\d{2}(?:[T ][^\s<]+)?", value)
    if match:
        value = match.group(0)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def scalar_url(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("@id", "url"):
            if isinstance(value.get(key), str):
                return value[key]
    return ""


def walk_json(value: object) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        title = next((clean(value.get(key)) for key in TITLE_KEYS if clean(value.get(key))), "")
        url = next((scalar_url(value.get(key)) for key in URL_KEYS if scalar_url(value.get(key))), "")
        date = next((clean(value.get(key)) for key in DATE_KEYS if clean(value.get(key))), "")
        if title and url and (date or str(value.get("@type", "")).lower() in {
            "article", "blogposting", "newsarticle", "scholarlyarticle"
        }):
            yield {"title": title, "url": url, "published_raw": date,
                   "summary": clean(value.get("description"))}
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


class IndexParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.items: list[dict[str, str]] = []
        self.json_scripts: list[str] = []
        self._json_depth = 0
        self._json_parts: list[str] = []
        self._article_depth = 0
        self._article: dict[str, str] | None = None
        self._anchor: dict[str, str] | None = None
        self._time_depth = 0
        self._time_parts: list[str] = []
        self._page_meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "script" and "ld+json" in values.get("type", "").lower():
            self._json_depth = 1
            self._json_parts = []
        elif self._json_depth and tag == "script":
            self._json_depth += 1
        if tag == "article":
            self._article_depth += 1
            if self._article_depth == 1:
                self._article = {"title": "", "url": "", "published_raw": "", "summary": ""}
        if tag == "a" and values.get("href"):
            self._anchor = {"url": urljoin(self.base_url, values["href"]), "text": ""}
        if tag == "time":
            self._time_depth = 1
            self._time_parts = []
            if self._article is not None and values.get("datetime"):
                self._article["published_raw"] = values["datetime"]
        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key and values.get("content"):
                self._page_meta[key] = values["content"]

    def handle_data(self, data: str) -> None:
        if self._json_depth:
            self._json_parts.append(data)
        if self._anchor is not None:
            self._anchor["text"] += data
        if self._time_depth:
            self._time_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_depth:
            self._json_depth -= 1
            if not self._json_depth:
                self.json_scripts.append("".join(self._json_parts))
        if tag == "a" and self._anchor is not None:
            title = clean(self._anchor["text"])
            url = self._anchor["url"]
            if self._article is not None and title and not self._article["title"]:
                self._article["title"], self._article["url"] = title, url
            elif self._article is None and plausible_link(title, url, self.base_url):
                self.items.append({"title": title, "url": url, "published_raw": "", "summary": ""})
            self._anchor = None
        if tag == "time" and self._time_depth:
            if self._article is not None and not self._article["published_raw"]:
                self._article["published_raw"] = clean("".join(self._time_parts))
            self._time_depth = 0
        if tag == "article" and self._article_depth:
            self._article_depth -= 1
            if self._article_depth == 0 and self._article is not None:
                if self._article["title"] and self._article["url"]:
                    self.items.append(self._article)
                self._article = None

    def extracted(self) -> list[dict[str, str]]:
        candidates = list(self.items)
        for raw in self.json_scripts:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for item in walk_json(payload):
                candidates.append({key: clean(value) for key, value in item.items()})
        title = self._page_meta.get("og:title") or self._page_meta.get("twitter:title")
        url = self._page_meta.get("og:url") or self.base_url
        date = self._page_meta.get("article:published_time") or self._page_meta.get("date")
        if title and date:
            candidates.append({"title": title, "url": url, "published_raw": date,
                               "summary": self._page_meta.get("og:description", "")})
        return deduplicate(candidates, self.base_url)


def plausible_link(title: str, url: str, base_url: str) -> bool:
    if len(title) < 8 or len(title) > 240 or url.startswith(("mailto:", "javascript:")):
        return False
    parsed, base = urlparse(url), urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc:
        return False
    path = parsed.path.lower().rstrip("/")
    return path not in {"", "/blog", "/research", "/news", "/engineering"}


def deduplicate(items: Iterable[dict[str, str]], base_url: str) -> list[dict[str, str]]:
    unique: dict[str, dict[str, str]] = {}
    for raw in items:
        item = dict(raw)
        item["url"] = urljoin(base_url, clean(item.get("url")))
        item["title"] = clean(item.get("title"))
        if not item["title"] or not item["url"]:
            continue
        key = item["url"].split("#", 1)[0].rstrip("/").casefold()
        prior = unique.get(key)
        if prior is None or (not prior.get("published_raw") and item.get("published_raw")):
            unique[key] = item
    return list(unique.values())


def parse_page(html: str, base_url: str) -> list[dict[str, str]]:
    parser = IndexParser(base_url)
    parser.feed(html)
    return parser.extracted()


def fetch(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def load_sources(path: Path, tiers: set[str], source_ids: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle)
                if row["access"] == "page" and row["tier"] in tiers
                and (not source_ids or row["id"] in source_ids)]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=root / "data" / "source-registry.csv")
    parser.add_argument("--output", type=Path, default=Path("page-candidates.jsonl"))
    parser.add_argument("--errors", type=Path, default=Path("page-errors.jsonl"))
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-per-source", type=int, default=30)
    parser.add_argument("--tiers", default="core,specialist")
    parser.add_argument("--source", action="append", default=[])
    args = parser.parse_args()
    if args.days < 1 or args.max_per_source < 1:
        parser.error("--days and --max-per-source must be positive")

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    sources = load_sources(args.registry, set(args.tiers.split(",")), set(args.source))
    candidates: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for source in sources:
        try:
            html = fetch(source["url"], args.timeout)
            kept = 0
            for item in parse_page(html, source["url"]):
                published = parse_date(item.get("published_raw"))
                if published is not None and published < cutoff:
                    continue
                candidates.append({
                    "title": item["title"], "url": item["url"],
                    "published_at": published.isoformat() if published else None,
                    "published_raw": item.get("published_raw") or None,
                    "summary": clean(item.get("summary"))[:2000],
                    "source_id": source["id"], "source_name": source["name"],
                    "source_tier": source["tier"], "axes": source["axes"].split("|"),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "needs_date_verification": published is None,
                })
                kept += 1
                if kept >= args.max_per_source:
                    break
        except (OSError, UnicodeError, urllib.error.URLError) as exc:
            errors.append({"source_id": source["id"], "url": source["url"], "error": str(exc)})

    for path, rows in ((args.output, candidates), (args.errors, errors)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Extracted {len(candidates)} candidates from {len(sources)} pages; {len(errors)} pages failed.")
    return 0 if candidates or not sources else 1


if __name__ == "__main__":
    raise SystemExit(main())

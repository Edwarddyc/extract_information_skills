#!/usr/bin/env python3
"""Validate required structure and self-contained styling of an AI radar HTML report."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_IDS = {
    "main", "priority-watch", "top-signals", "research-axes", "axis-framework",
    "axis-evaluation", "axis-evolution", "axis-product", "synthesis",
    "random-signal", "queue", "source-health",
}
REQUIRED_WATCH_SOURCES = {
    "claude-blog", "anthropic-research", "openai-engineering", "openai-research",
    "openai-news", "hermes-repo", "pi-agent", "deepseek-harness", "agno-repo",
    "langchain-repo", "langgraph-repo", "langchain-blog", "langfuse-repo",
    "langfuse-blog",
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
ALLOWED_WATCH_STATES = {"material-update", "no-material-update", "inaccessible"}
WATCH_STATES = {"material-update", "no-material-update"}
SOURCE_LOCATIONS = {"priority-watch", "source-health"}
EXTERNAL_FRAMEWORK_SOURCES = {
    "pydantic-ai", "google-adk", "microsoft-agent-framework", "openhands",
    "letta-code", "a2a-spec", "otel-genai-semconv", "mcp-spec", "strands-agents",
}
ALLOWED_STUDY_TYPES = {"cross-framework", "mechanism", "standard", "failure-analysis"}
ALLOWED_PAPER_POOLS = {"weekly-hot", "fresh-exploration", "quota-backfill"}
FRAMEWORK_SOURCE_PREFIXES = {
    "pydantic-ai": ("https://github.com/pydantic/pydantic-ai", "https://ai.pydantic.dev"),
    "google-adk": ("https://github.com/google/adk-python", "https://google.github.io/adk-docs"),
    "microsoft-agent-framework": ("https://github.com/microsoft/agent-framework",),
    "openhands": (
        "https://github.com/openhands/openhands",
        "https://github.com/openhands/docs",
        "https://docs.openhands.dev",
    ),
    "letta-code": (
        "https://github.com/letta-ai/letta-code",
        "https://github.com/letta-ai/letta",
        "https://docs.letta.com",
    ),
    "a2a-spec": ("https://github.com/a2aproject/a2a", "https://a2a-protocol.org"),
    "otel-genai-semconv": (
        "https://github.com/open-telemetry/semantic-conventions-genai",
        "https://opentelemetry.io",
    ),
    "mcp-spec": (
        "https://github.com/modelcontextprotocol/specification",
        "https://github.com/modelcontextprotocol/modelcontextprotocol",
        "https://modelcontextprotocol.io",
    ),
    "strands-agents": (
        "https://github.com/strands-agents/sdk-python",
        "https://strandsagents.com",
    ),
}


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.external_assets: list[str] = []
        self.scripts = 0
        self.links: list[str] = []
        self.has_title = False
        self.watch_sources: dict[str, tuple[str, str, str]] = {}
        self.watch_organizations: dict[str, dict[str, object]] = {}
        self.active_watch_org = ""
        self.watch_popover_ids: list[str] = []
        self.signal_records: list[dict[str, int]] = []
        self.active_signal: int | None = None
        self.framework_studies: list[dict[str, object]] = []
        self.active_framework_study: int | None = None
        self.framework_empty_count = 0
        self.paper_items: list[dict[str, object]] = []
        self.active_paper_item: int | None = None
        self.section_stack: list[str] = []

    def record_source(self, source_id: str, state: str, location: str, section: str) -> None:
        if source_id in self.watch_sources:
            self.watch_sources[source_id] = ("duplicate", "duplicate", "duplicate")
        else:
            self.watch_sources[source_id] = (state, location, section)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if tag == "section":
            self.section_stack.append(values.get("id") or "")
        section = next((item for item in reversed(self.section_stack) if item), "")
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "title":
            self.has_title = True
        if tag == "script":
            self.scripts += 1
            if values.get("src"):
                self.external_assets.append(values["src"] or "")
        if tag == "link" and values.get("href"):
            relation = (values.get("rel") or "").lower()
            if "stylesheet" in relation:
                self.external_assets.append(values["href"] or "")
        if tag in {"img", "source", "video", "audio", "iframe"} and values.get("src"):
            source = values["src"] or ""
            if urlparse(source).scheme in {"http", "https"}:
                self.external_assets.append(source)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if "watch-org" in classes:
            organization = values.get("data-organization") or ""
            source_ids = [
                source_id.strip()
                for source_id in (values.get("data-source-ids") or "").split(",")
                if source_id.strip()
            ]
            if organization in self.watch_organizations:
                self.watch_organizations[organization]["duplicate"] = True
            else:
                self.watch_organizations[organization] = {
                    "state": values.get("data-state") or "",
                    "location": values.get("data-location") or "",
                    "section": section,
                    "source_ids": source_ids,
                    "additional_count": values.get("data-additional-count") or "",
                    "primary_count": 0,
                    "secondary_count": 0,
                    "trigger_count": 0,
                    "popover_count": 0,
                    "close_count": 0,
                    "all_item_count": 0,
                    "all_link_count": 0,
                    "trigger_target": "",
                    "popover_id": "",
                    "close_target": "",
                    "duplicate": False,
                }
            self.active_watch_org = organization
            for source_id in source_ids:
                self.record_source(
                    source_id,
                    values.get("data-state") or "",
                    values.get("data-location") or "",
                    section,
                )
        if tag == "article" and "signal" in classes:
            self.signal_records.append({
                "number": 0,
                "meta": 0,
                "change": 0,
                "field": 0,
                "source": 0,
            })
            self.active_signal = len(self.signal_records) - 1
        if tag == "article" and "framework-study" in classes:
            source_ids = [
                source_id.strip()
                for source_id in (values.get("data-source-ids") or "").split(",")
                if source_id.strip()
            ]
            self.framework_studies.append({
                "type": values.get("data-study-type") or "",
                "source_ids": source_ids,
                "section": section,
                "meta": 0,
                "findings": 0,
                "question": 0,
                "mechanism": 0,
                "comparison": 0,
                "sources": 0,
                "source_links": 0,
                "typed_source_links": 0,
                "source_hrefs": [],
            })
            self.active_framework_study = len(self.framework_studies) - 1
        if tag == "article" and "paper-item" in classes:
            self.paper_items.append({
                "pool": values.get("data-paper-pool") or "",
                "heat_score": values.get("data-heat-score") or "",
                "relevance_score": values.get("data-relevance-score") or "",
                "section": section,
                "meta": 0,
                "links": 0,
            })
            self.active_paper_item = len(self.paper_items) - 1
        if "framework-empty" in classes and section == "axis-framework":
            self.framework_empty_count += 1
        if self.active_signal is not None:
            signal = self.signal_records[self.active_signal]
            if "signal-number" in classes:
                signal["number"] += 1
            if "signal-meta" in classes:
                signal["meta"] += 1
            if "signal-change" in classes:
                signal["change"] += 1
            if "signal-field" in classes:
                signal["field"] += 1
            if "signal-source" in classes:
                signal["source"] += 1
        if self.active_framework_study is not None:
            study = self.framework_studies[self.active_framework_study]
            if "study-meta" in classes:
                study["meta"] = int(study["meta"]) + 1
            if "study-findings" in classes:
                study["findings"] = int(study["findings"]) + 1
            if "study-question" in classes:
                study["question"] = int(study["question"]) + 1
            if "study-mechanism" in classes:
                study["mechanism"] = int(study["mechanism"]) + 1
            if "study-comparison" in classes:
                study["comparison"] = int(study["comparison"]) + 1
            if "study-sources" in classes:
                study["sources"] = int(study["sources"]) + 1
            if tag == "a" and "study-source" in classes:
                study["source_links"] = int(study["source_links"]) + 1
                href = values.get("href") or ""
                study["source_hrefs"].append(href)
                if (
                    values.get("data-evidence-type")
                    and urlparse(href).scheme in {"http", "https"}
                ):
                    study["typed_source_links"] = int(study["typed_source_links"]) + 1
        if self.active_paper_item is not None:
            paper = self.paper_items[self.active_paper_item]
            if "paper-selection-meta" in classes:
                paper["meta"] = int(paper["meta"]) + 1
            if tag == "a" and urlparse(values.get("href") or "").scheme in {"http", "https"}:
                paper["links"] = int(paper["links"]) + 1
        if tag == "a" and self.active_watch_org in self.watch_organizations:
            record = self.watch_organizations[self.active_watch_org]
            if "watch-primary" in classes:
                record["primary_count"] = int(record["primary_count"]) + 1
            if "watch-secondary" in classes:
                record["secondary_count"] = int(record["secondary_count"]) + 1
            if "watch-all-link" in classes:
                record["all_link_count"] = int(record["all_link_count"]) + 1
        if self.active_watch_org in self.watch_organizations:
            record = self.watch_organizations[self.active_watch_org]
            if "watch-all-trigger" in classes:
                record["trigger_count"] = int(record["trigger_count"]) + 1
                record["trigger_target"] = values.get("popovertarget") or ""
            if "watch-popover" in classes:
                record["popover_count"] = int(record["popover_count"]) + 1
                record["popover_id"] = values.get("id") or ""
                self.watch_popover_ids.append(values.get("id") or "")
            if "watch-popover-close" in classes:
                record["close_count"] = int(record["close_count"]) + 1
                record["close_target"] = values.get("popovertarget") or ""
            if "watch-all-item" in classes:
                record["all_item_count"] = int(record["all_item_count"]) + 1
        if values.get("data-source-id"):
            source_id = values["data-source-id"] or ""
            self.record_source(
                source_id,
                values.get("data-state") or "",
                values.get("data-location") or "",
                section,
            )

    def handle_endtag(self, tag: str) -> None:
        if tag == "article" and self.active_watch_org:
            self.active_watch_org = ""
        if tag == "article" and self.active_signal is not None:
            self.active_signal = None
        if tag == "article" and self.active_framework_study is not None:
            self.active_framework_study = None
        if tag == "article" and self.active_paper_item is not None:
            self.active_paper_item = None
        if tag == "section" and self.section_stack:
            self.section_stack.pop()


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    parser = ReportParser()
    parser.feed(text)

    placeholders = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", text)))
    if placeholders:
        errors.append(f"unresolved placeholders: {', '.join(placeholders[:8])}")
    missing_ids = sorted(REQUIRED_IDS - parser.ids)
    if missing_ids:
        errors.append(f"missing required section ids: {', '.join(missing_ids)}")
    if not parser.has_title:
        errors.append("missing document title")
    if parser.external_assets:
        errors.append(f"external visual assets are not allowed: {', '.join(parser.external_assets[:5])}")
    if parser.scripts:
        errors.append("report must not contain JavaScript")
    if not any(urlparse(link).scheme in {"http", "https"} for link in parser.links):
        errors.append("report has no public source links")
    if "<meta name=\"viewport\"" not in text and "<meta name='viewport'" not in text:
        errors.append("missing viewport metadata")
    if "@media print" not in text:
        errors.append("missing print stylesheet")
    missing_watch = sorted(REQUIRED_WATCH_SOURCES - set(parser.watch_sources))
    if missing_watch:
        errors.append(f"missing priority watch sources: {', '.join(missing_watch)}")
    invalid_watch = sorted(
        source_id for source_id, (state, location, _section) in parser.watch_sources.items()
        if source_id in REQUIRED_WATCH_SOURCES
        and (state not in ALLOWED_WATCH_STATES or location not in SOURCE_LOCATIONS)
    )
    if invalid_watch:
        errors.append(f"invalid or duplicate priority source record: {', '.join(invalid_watch)}")
    misplaced_watch = sorted(
        source_id for source_id, (state, location, section) in parser.watch_sources.items()
        if source_id in REQUIRED_WATCH_SOURCES
        and (
            (state in WATCH_STATES and (location != "priority-watch" or section != "priority-watch"))
            or (state == "inaccessible" and (location != "source-health" or section != "source-health"))
        )
    )
    if misplaced_watch:
        errors.append(f"priority source state is in the wrong section: {', '.join(misplaced_watch)}")
    invalid_organization_sources = sorted(
        source_id
        for organization, record in parser.watch_organizations.items()
        for source_id in record["source_ids"]
        if SOURCE_ORGANIZATIONS.get(str(source_id)) != organization
    )
    if invalid_organization_sources:
        errors.append(
            "priority sources assigned to the wrong organization: "
            + ", ".join(invalid_organization_sources)
        )
    expected_organizations = {
        SOURCE_ORGANIZATIONS[source_id]
        for source_id, (state, _location, _section) in parser.watch_sources.items()
        if source_id in SOURCE_ORGANIZATIONS and state in WATCH_STATES
    }
    missing_organizations = sorted(expected_organizations - set(parser.watch_organizations))
    if missing_organizations:
        errors.append(f"missing priority organizations: {', '.join(missing_organizations)}")
    invalid_organizations: list[str] = []
    for organization, record in parser.watch_organizations.items():
        try:
            additional_count = int(str(record["additional_count"]))
        except ValueError:
            additional_count = -1
        state = str(record["state"])
        primary_count = int(record["primary_count"])
        secondary_count = int(record["secondary_count"])
        trigger_count = int(record["trigger_count"])
        popover_count = int(record["popover_count"])
        close_count = int(record["close_count"])
        all_item_count = int(record["all_item_count"])
        all_link_count = int(record["all_link_count"])
        popover_id = str(record["popover_id"])
        valid_popover = (
            (
                additional_count > 0
                and trigger_count == 1
                and popover_count == 1
                and close_count == 1
                and all_item_count == additional_count
                and all_link_count == additional_count
                and popover_id
                and record["trigger_target"] == popover_id
                and record["close_target"] == popover_id
            )
            or (
                additional_count == 0
                and trigger_count == 0
                and popover_count == 0
                and close_count == 0
                and all_item_count == 0
                and all_link_count == 0
            )
        )
        if (
            record["duplicate"]
            or state not in WATCH_STATES
            or record["location"] != "priority-watch"
            or record["section"] != "priority-watch"
            or not record["source_ids"]
            or additional_count < secondary_count
            or secondary_count > 3
            or not valid_popover
            or (state == "material-update" and primary_count != 1)
            or (
                state == "no-material-update"
                and (primary_count != 0 or secondary_count != 0 or additional_count != 0)
            )
        ):
            invalid_organizations.append(organization or "missing-organization")
    if invalid_organizations:
        errors.append(
            "invalid priority organization summary: "
            + ", ".join(sorted(invalid_organizations))
        )
    if len(parser.watch_popover_ids) != len(set(parser.watch_popover_ids)):
        errors.append("priority update popover ids must be unique")
    if not 1 <= len(parser.signal_records) <= 5:
        errors.append("report must contain between one and five Top Signals")
    invalid_signals = [
        str(index)
        for index, record in enumerate(parser.signal_records, start=1)
        if record != {"number": 1, "meta": 1, "change": 1, "field": 3, "source": 1}
    ]
    if invalid_signals:
        errors.append(
            "invalid Top Signal structure at positions: " + ", ".join(invalid_signals)
        )
    if len(parser.framework_studies) > 3:
        errors.append("Agent Framework must contain at most three research notes")
    if parser.framework_studies and parser.framework_empty_count:
        errors.append("Agent Framework cannot mix research notes with an empty state")
    if not parser.framework_studies and parser.framework_empty_count != 1:
        errors.append("Agent Framework requires research notes or one explicit empty state")
    invalid_studies: list[str] = []
    for index, study in enumerate(parser.framework_studies, start=1):
        source_ids = [str(source_id) for source_id in study["source_ids"]]
        source_hrefs = [str(href).lower() for href in study["source_hrefs"]]
        sources_with_evidence = {
            source_id
            for source_id in source_ids
            if any(
                href.startswith(prefix.lower())
                for href in source_hrefs
                for prefix in FRAMEWORK_SOURCE_PREFIXES.get(source_id, ())
            )
        }
        if (
            study["section"] != "axis-framework"
            or study["type"] not in ALLOWED_STUDY_TYPES
            or not source_ids
            or len(source_ids) != len(set(source_ids))
            or not set(source_ids) <= EXTERNAL_FRAMEWORK_SOURCES
            or (study["type"] == "cross-framework" and len(source_ids) < 2)
            or study["meta"] != 1
            or study["findings"] != 1
            or study["question"] != 1
            or study["mechanism"] != 1
            or study["comparison"] != 1
            or study["sources"] != 1
            or study["source_links"] < 2
            or study["source_links"] != study["typed_source_links"]
            or sources_with_evidence != set(source_ids)
        ):
            invalid_studies.append(str(index))
    if invalid_studies:
        errors.append(
            "invalid Agent Framework research note at positions: "
            + ", ".join(invalid_studies)
        )
    invalid_papers: list[str] = []
    for index, paper in enumerate(parser.paper_items, start=1):
        try:
            heat_score = float(str(paper["heat_score"]))
            relevance_score = float(str(paper["relevance_score"]))
        except ValueError:
            heat_score = relevance_score = -1.0
        if (
            paper["section"] not in {"axis-framework", "axis-evaluation", "axis-evolution"}
            or paper["pool"] not in ALLOWED_PAPER_POOLS
            or not 0 <= heat_score <= 100
            or not 0 <= relevance_score <= 100
            or paper["meta"] != 1
            or int(paper["links"]) < 1
        ):
            invalid_papers.append(str(index))
    if invalid_papers:
        errors.append("invalid paper item at positions: " + ", ".join(invalid_papers))
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_html_report.py <report.html>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Report not found: {path}", file=sys.stderr)
        return 2
    errors = validate(path)
    if errors:
        print("HTML report validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"HTML report valid: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

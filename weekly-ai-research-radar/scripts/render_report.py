#!/usr/bin/env python3
"""Render a validated weekly report from structured JSON or YAML data."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


ORG_ORDER = ["anthropic", "openai", "hermes", "pi", "deepseek-harness", "agno", "langchain", "langfuse"]
ORG_LABELS = {"anthropic": "Anthropic", "openai": "OpenAI", "hermes": "Hermes", "pi": "Pi",
              "deepseek-harness": "DeepSeek Harness", "agno": "Agno", "langchain": "LangChain", "langfuse": "Langfuse"}
POOL_LABELS = {"weekly-hot": "本周高热", "fresh-exploration": "最新探索", "quota-backfill": "配额回填"}


def e(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def require_url(value: object, field: str) -> str:
    url = str(value or "").strip()
    if urlparse(url).scheme not in {"http", "https"}:
        raise ValueError(f"{field} must be an http(s) URL")
    return e(url)


def load_data(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML input requires PyYAML; use JSON or install PyYAML") from exc
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("input must end in .json, .yaml, or .yml")
    if not isinstance(value, dict):
        raise ValueError("report data must be an object")
    return value


def paragraphs(values: object) -> str:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list) or not values:
        return "<p>无。</p>"
    return "".join(f"<p>{e(value)}</p>" for value in values)


def render_priority(records: list[dict[str, Any]]) -> tuple[str, str]:
    accessible = [record for record in records if record.get("state") != "inaccessible"]
    inaccessible = [record for record in records if record.get("state") == "inaccessible"]
    modules: list[str] = []
    for organization in ORG_ORDER:
        group = [record for record in accessible if record.get("organization") == organization]
        if not group:
            continue
        updates = [dict(update, _source=record.get("name", record.get("source_id", "")))
                   for record in group for update in record.get("updates", [])]
        state = "material-update" if any(record.get("state") == "material-update" for record in group) else "no-material-update"
        checked = max((str(record.get("checked_at", "")) for record in group), default="")
        source_ids = ",".join(str(record.get("source_id", "")) for record in group)
        label = ORG_LABELS.get(organization, organization)
        head = (f'<article class="watch-org" data-organization="{e(organization)}" '
                f'data-source-ids="{e(source_ids)}" data-state="{state}" '
                f'data-location="priority-watch" data-additional-count="{max(0, len(updates)-1)}">'
                f'<header class="watch-org-head"><h3>{e(label)}</h3>'
                f'<time datetime="{e(checked[:10])}">{e(checked[:10])}</time></header>')
        if state == "no-material-update":
            modules.append(head + "<p>No material update.</p></article>")
            continue
        if not updates:
            raise ValueError(f"material-update organization {organization} has no updates")
        primary_index = next((index for index, update in enumerate(updates) if update.get("primary")), 0)
        primary = updates.pop(primary_index)
        body = (f'<div class="watch-primary-block"><p class="watch-label">本周最重要</p>'
                f'<h4><a class="watch-primary" href="{require_url(primary.get("url"), "priority update url")}">{e(primary.get("title"))}</a></h4>'
                f'<p>{e(primary.get("implication", ""))}</p></div>')
        if updates:
            popover_id = f"updates-{organization}"
            secondary = "".join(
                f'<li><a class="watch-secondary" href="{require_url(item.get("url"), "priority update url")}">{e(item.get("title"))}</a></li>'
                for item in updates[:3]
            )
            all_items = "".join(
                f'<li class="watch-all-item"><a class="watch-all-link" href="{require_url(item.get("url"), "priority update url")}">{e(item.get("title"))}</a>'
                f'<time datetime="{e(str(item.get("date", ""))[:10])}">{e(str(item.get("date", ""))[:10])}</time>'
                f'<span class="watch-all-source">{e(item.get("source") or item.get("_source"))}</span></li>'
                for item in updates
            )
            body += (f'<div class="watch-more"><div class="watch-more-head"><p><strong>另有 {len(updates)} 项更新</strong></p>'
                     f'<button class="watch-all-trigger" type="button" popovertarget="{popover_id}">查看全部 {len(updates)} 项</button></div>'
                     f'<ul>{secondary}</ul><div class="watch-popover" id="{popover_id}" popover>'
                     f'<header class="watch-popover-head"><h4>{e(label)} · 其他 {len(updates)} 项更新</h4>'
                     f'<button class="watch-popover-close" type="button" popovertarget="{popover_id}" popovertargetaction="hide" aria-label="关闭全部更新">×</button></header>'
                     f'<ol class="watch-all-list">{all_items}</ol></div></div>')
        modules.append(head + body + "</article>")

    health = "".join(
        f'<article class="health-source" data-source-id="{e(record.get("source_id"))}" data-state="inaccessible" data-location="source-health">'
        f'<h4>{e(record.get("name") or record.get("source_id"))}</h4><p>{e(record.get("checked_at", ""))} 检查失败：{e(record.get("failure", "未说明"))}。'
        f'官方替代检查：{e(record.get("fallback", "未找到"))}。</p></article>'
        for record in inaccessible
    )
    return "".join(modules), health


def render_signals(records: list[dict[str, Any]]) -> str:
    if not 1 <= len(records) <= 5:
        raise ValueError("top_signals must contain 1-5 records")
    return "".join(
        f'<article class="signal"><span class="signal-number">{index:02d}</span><div class="signal-body">'
        f'<p class="signal-meta">{e(item.get("axis"))} · {e(item.get("score"))}/100 · {e(item.get("confidence"))}</p>'
        f'<h3>{e(item.get("title"))}</h3><div class="signal-change"><span class="signal-label">发生了什么</span><p>{e(item.get("change"))}</p></div>'
        f'<dl><div class="signal-field"><dt>为什么与你有关</dt><dd>{e(item.get("impact"))}</dd></div>'
        f'<div class="signal-field"><dt>证据与限制</dt><dd>{e(item.get("evidence"))}</dd></div>'
        f'<div class="signal-field"><dt>建议动作</dt><dd>{e(item.get("action"))}</dd></div></dl>'
        f'<a class="signal-source" href="{require_url(item.get("url"), "top signal url")}">查看原始来源 →</a></div></article>'
        for index, item in enumerate(records, 1)
    )


def render_paper_summary(value: dict[str, Any]) -> str:
    if not value:
        return "<p>本期没有论文进入组合。</p>"
    return (f'<p>候选窗口 {e(value.get("candidate_window", "30 days"))}；热度窗口 {e(value.get("heat_window", "7 days"))}。'
            f'目标 hot/fresh：{e(value.get("requested_hot", 7))}/{e(value.get("requested_fresh", 3))}；'
            f'实际：{e(value.get("selected_hot", 0))}/{e(value.get("selected_fresh", 0))}；'
            f'回填 {e(value.get("backfill", 0))}。</p>')


def render_framework(axis: dict[str, Any]) -> str:
    studies = axis.get("studies") or []
    if not studies:
        return f'<p class="framework-empty">No material signal：{e(axis.get("empty_reason", "已检查外部框架来源，证据不足。"))}</p>'
    if len(studies) > 3:
        raise ValueError("axes.framework.studies supports at most 3 records")
    blocks = []
    for index, study in enumerate(studies, 1):
        sources = "".join(
            f'<li><a class="study-source" data-evidence-type="{e(source.get("evidence_type"))}" href="{require_url(source.get("url"), "framework source url")}">{e(source.get("label"))}</a></li>'
            for source in study.get("sources", [])
        )
        blocks.append(
            f'<article class="framework-study" data-study-type="{e(study.get("type"))}" data-source-ids="{e(",".join(study.get("source_ids", [])))}">'
            f'<p class="study-meta">Research note {index:02d} · {e(study.get("confidence"))}</p><h4>{e(study.get("title"))}</h4>'
            f'<dl class="study-findings"><div class="study-question"><dt>研究问题</dt><dd>{e(study.get("question"))}</dd></div>'
            f'<div class="study-mechanism"><dt>机制发现</dt><dd>{e(study.get("mechanism"))}</dd></div>'
            f'<div class="study-comparison"><dt>比较与边界</dt><dd>{e(study.get("comparison"))}</dd></div></dl>'
            f'<footer class="study-sources"><p>数据来源</p><ol>{sources}</ol></footer></article>'
        )
    return "".join(blocks)


def render_axis_items(axis: dict[str, Any]) -> str:
    items = axis.get("items") or []
    if not items:
        return f'<article class="axis-item"><h4>No material signal</h4><p>{e(axis.get("empty_reason", "已检查相关来源，无项目越过阈值。"))}</p></article>'
    blocks = []
    for item in items:
        classes, attrs, meta = "axis-item", "", ""
        if item.get("paper_pool"):
            pool = str(item["paper_pool"])
            classes += " paper-item"
            attrs = f' data-paper-pool="{e(pool)}" data-heat-score="{e(item.get("heat_score"))}" data-relevance-score="{e(item.get("relevance_score"))}"'
            meta = f'<div class="paper-selection-meta"><span class="paper-pool">{e(POOL_LABELS.get(pool, pool))}</span><span>Heat {e(item.get("heat_score"))} · Research fit {e(item.get("relevance_score"))}</span></div>'
        blocks.append(f'<article class="{classes}"{attrs}>{meta}<h4>{e(item.get("title"))}</h4><p>{e(item.get("body"))}</p><a href="{require_url(item.get("url"), "axis item url")}">原始来源 →</a></article>')
    return "".join(blocks)


def render_synthesis(records: list[dict[str, Any]]) -> str:
    if not records:
        return "<p>本期没有足够证据支持跨信号连接。</p>"
    return "".join(f'<article><span class="relation">{e(item.get("relation"))}</span><h3>{e(item.get("title"))}</h3><p>{e(item.get("body"))}</p></article>' for item in records)


def render_queue(records: list[dict[str, Any]]) -> str:
    return "".join(f'<tr><td>{index:02d}</td><td>{e(item.get("type"))}</td><td>{e(item.get("artifact"))}</td><td>{e(item.get("outcome"))}</td></tr>' for index, item in enumerate(records, 1))


def render_random_links(value: dict[str, Any]) -> str:
    links = []
    if value.get("source_url"):
        links.append(f'<a href="{require_url(value.get("source_url"), "random source url")}">原始提交 →</a>')
    if value.get("discussion_url"):
        links.append(f'<a href="{require_url(value.get("discussion_url"), "random discussion url")}">HN 讨论 →</a>')
    return "".join(links) if links else "<span>本期无可访问的合格条目。</span>"


def render_extra_health(records: list[dict[str, Any]]) -> str:
    return "".join(f'<article class="health-source"><h4>{e(item.get("name") or item.get("source_id"))}</h4><p>{e(item.get("checked_at", ""))}：{e(item.get("failure"))}。替代检查：{e(item.get("fallback"))}。</p></article>' for item in records)


def replacements(data: dict[str, Any]) -> dict[str, str]:
    if "html_fragments" in data:
        raise ValueError("html_fragments is not supported; provide structured report fields")
    meta = data.get("meta") or {}
    axes = data.get("axes") or {}
    priority, priority_health = render_priority(data.get("priority_watch") or [])
    random = data.get("random_signal") or {}
    values = {
        "REPORT_TITLE": e(meta.get("title")), "DATE_RANGE": e(meta.get("date_range")),
        "REPORT_END_ISO": e(meta.get("report_end")), "ISSUE_NUMBER": e(meta.get("issue_number")),
        "GENERATED_AT": e(meta.get("generated_at")), "REPORT_DECK": e(meta.get("deck")),
        "RETAINED_COUNT": e(meta.get("retained_count")), "CANDIDATE_COUNT": e(meta.get("candidate_count")),
        "EXECUTIVE_JUDGMENT": e(meta.get("executive_judgment")),
        "PRIORITY_ORGANIZATIONS_HTML": priority, "TOP_SIGNALS_HTML": render_signals(data.get("top_signals") or []),
        "PAPER_PORTFOLIO_SUMMARY_HTML": render_paper_summary(data.get("paper_portfolio") or {}),
        "FRAMEWORK_STATUS": e((axes.get("framework") or {}).get("status", "No material signal")),
        "FRAMEWORK_STUDIES_HTML": render_framework(axes.get("framework") or {}),
        "EVALUATION_STATUS": e((axes.get("evaluation") or {}).get("status", "No material signal")),
        "EVALUATION_ITEMS_HTML": render_axis_items(axes.get("evaluation") or {}),
        "EVOLUTION_STATUS": e((axes.get("evolution") or {}).get("status", "No material signal")),
        "EVOLUTION_ITEMS_HTML": render_axis_items(axes.get("evolution") or {}),
        "PRODUCT_STATUS": e((axes.get("product") or {}).get("status", "No material signal")),
        "PRODUCT_ITEMS_HTML": render_axis_items(axes.get("product") or {}),
        "SYNTHESIS_HTML": render_synthesis(data.get("synthesis") or []),
        "RANDOM_SEED": e(random.get("seed")), "RANDOM_TITLE": e(random.get("title")),
        "RANDOM_TENSION": e(random.get("tension")), "RANDOM_EVIDENCE": e(random.get("evidence")),
        "RANDOM_LINKS_HTML": render_random_links(random),
        "RESEARCH_QUEUE_ROWS_HTML": render_queue(data.get("research_queue") or []),
        "CORE_SOURCE_HEALTH_HTML": priority_health + render_extra_health(data.get("source_health") or []),
        "COVERAGE_GAPS_HTML": paragraphs(data.get("coverage_gaps") or []),
        "REGISTRY_CHANGES_HTML": paragraphs(data.get("registry_changes") or []),
    }
    return values


def render(data: dict[str, Any], template: str) -> str:
    values = replacements(data)
    missing = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template)) - set(values))
    if missing:
        raise ValueError("renderer has no value for placeholders: " + ", ".join(missing))
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda match: values[match.group(1)], template)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=root / "assets" / "weekly-report-template.html")
    parser.add_argument("--no-validate", action="store_true")
    args = parser.parse_args()
    try:
        result = render(load_data(args.input), args.template.read_text(encoding="utf-8"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8", newline="\n")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 2
    if not args.no_validate:
        completed = subprocess.run([sys.executable, str(root / "scripts" / "validate_html_report.py"), str(args.output)])
        if completed.returncode:
            return completed.returncode
    print(f"Rendered report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

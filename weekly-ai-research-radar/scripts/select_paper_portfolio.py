#!/usr/bin/env python3
"""Select a 70/30 weekly paper portfolio from public, no-key heat signals."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


def parse_datetime(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.combine(date.fromisoformat(value), datetime.min.time())
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def number(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def canonical_key(candidate: dict[str, Any]) -> str:
    explicit = str(candidate.get("canonical_id") or "").strip().lower()
    if explicit:
        return explicit
    url = str(candidate.get("url") or "").strip()
    if not url:
        return str(candidate.get("title") or "").strip().casefold()
    parts = urlsplit(url)
    path = parts.path.rstrip("/")
    if "arxiv.org" in parts.netloc.lower():
        path = path.replace("/pdf/", "/abs/").removesuffix(".pdf")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def heat_details(candidate: dict[str, Any]) -> tuple[float, int, dict[str, float]]:
    signals = candidate.get("heat_signals")
    heat = signals if isinstance(signals, dict) else candidate

    hf_rank = number(heat.get("hf_weekly_rank"))
    hf_upvotes = number(heat.get("hf_upvotes_7d"))
    hf_rank_points = max(0.0, 21.0 - hf_rank) if 1 <= hf_rank <= 20 else 0.0
    hf_vote_points = min(max(hf_upvotes, 0.0) / 100.0, 1.0) * 15.0
    hf_points = min(35.0, hf_rank_points + hf_vote_points)

    independent_sources = int(max(0.0, number(heat.get("independent_sources_7d"))))
    cross_source_points = min(max(independent_sources - 1, 0) / 3.0, 1.0) * 25.0

    github_trending = bool(heat.get("github_weekly_trending", False))
    github_stars = max(0.0, number(heat.get("github_stars_7d")))
    github_points = 20.0 if github_trending else min(github_stars / 100.0, 1.0) * 20.0

    academic_discussions = max(0.0, number(heat.get("academic_discussions_7d")))
    academic_points = min(academic_discussions / 10.0, 1.0) * 10.0

    current_attention = max(0.0, number(heat.get("attention_events_7d")))
    previous_attention = max(0.0, number(heat.get("attention_events_previous_7d")))
    acceleration_points = 0.0
    if current_attention > previous_attention:
        acceleration_points = min(
            (current_attention - previous_attention) / current_attention, 1.0
        ) * 10.0

    observed_channels = 0
    observed_channels += int(hf_points > 0)
    observed_channels += int(independent_sources >= 2)
    observed_channels += int(github_points > 0)
    observed_channels += int(academic_points > 0)
    observed_channels += int(current_attention > 0)
    signal_count = max(independent_sources, observed_channels)

    components = {
        "huggingface": round(hf_points, 2),
        "cross_source": round(cross_source_points, 2),
        "github": round(github_points, 2),
        "academic_discussion": round(academic_points, 2),
        "attention_acceleration": round(acceleration_points, 2),
    }
    return round(sum(components.values()), 2), signal_count, components


def deduplicate(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        key = canonical_key(candidate)
        if not key:
            continue
        heat_score, _, _ = heat_details(candidate)
        quality = (number(candidate.get("relevance_score")), heat_score)
        incumbent = best.get(key)
        if incumbent is None:
            best[key] = candidate
            continue
        incumbent_quality = (
            number(incumbent.get("relevance_score")),
            heat_details(incumbent)[0],
        )
        if quality > incumbent_quality:
            best[key] = candidate
    return list(best.values())


def quota(total: int, hot_ratio: float) -> tuple[int, int]:
    hot = int(math.floor(total * hot_ratio + 0.5))
    return hot, total - hot


def select_portfolio(
    candidates: Iterable[dict[str, Any]],
    report_end: date,
    limit: int = 10,
    candidate_days: int = 30,
    fresh_days: int = 7,
    hot_ratio: float = 0.7,
    min_heat_score: float = 40.0,
    min_independent_signals: int = 2,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidate_start = report_end - timedelta(days=candidate_days - 1)
    fresh_start = report_end - timedelta(days=fresh_days - 1)
    eligible: list[dict[str, Any]] = []

    for original in deduplicate(candidates):
        published = parse_datetime(original.get("published_at") or original.get("published_date"))
        if published is None or not candidate_start <= published.date() <= report_end:
            continue
        item = dict(original)
        heat_score, signal_count, components = heat_details(item)
        item["heat_score"] = heat_score
        item["heat_signal_count"] = signal_count
        item["heat_components"] = components
        item["published_date"] = published.date().isoformat()
        eligible.append(item)

    hot_target, exploration_target = quota(limit, hot_ratio)
    hot_candidates = sorted(
        (
            item for item in eligible
            if item["heat_score"] >= min_heat_score
            and item["heat_signal_count"] >= min_independent_signals
        ),
        key=lambda item: (
            number(item.get("heat_score")),
            number(item.get("relevance_score")),
            item["published_date"],
        ),
        reverse=True,
    )
    selected_hot = hot_candidates[:hot_target]
    selected_keys = {canonical_key(item) for item in selected_hot}

    exploration_candidates = sorted(
        (
            item for item in eligible
            if canonical_key(item) not in selected_keys
            and fresh_start <= date.fromisoformat(item["published_date"]) <= report_end
        ),
        key=lambda item: (
            number(item.get("relevance_score")),
            item["published_date"],
            number(item.get("heat_score")),
        ),
        reverse=True,
    )
    selected_exploration = exploration_candidates[:exploration_target]
    selected_keys.update(canonical_key(item) for item in selected_exploration)

    # Fill a short quota from the other genuine pool before using broad backfill.
    slots_left = max(0, limit - len(selected_hot) - len(selected_exploration))
    extra_exploration = [
        item for item in exploration_candidates
        if canonical_key(item) not in selected_keys
    ][:slots_left]
    selected_exploration.extend(extra_exploration)
    selected_keys.update(canonical_key(item) for item in extra_exploration)

    slots_left = max(0, limit - len(selected_hot) - len(selected_exploration))
    extra_hot = [
        item for item in hot_candidates
        if canonical_key(item) not in selected_keys
    ][:slots_left]
    selected_hot.extend(extra_hot)
    selected_keys.update(canonical_key(item) for item in extra_hot)

    # Preserve output size when both qualified pools are short, with an explicit label.
    remaining = sorted(
        (item for item in eligible if canonical_key(item) not in selected_keys),
        key=lambda item: (
            number(item.get("relevance_score")),
            number(item.get("heat_score")),
            item["published_date"],
        ),
        reverse=True,
    )
    backfill = remaining[: max(0, limit - len(selected_hot) - len(selected_exploration))]

    selected: list[dict[str, Any]] = []
    for pool, items in (
        ("weekly-hot", selected_hot),
        ("fresh-exploration", selected_exploration),
        ("quota-backfill", backfill),
    ):
        for item in items:
            output = dict(item)
            output["paper_pool"] = pool
            output["selection_rank"] = len(selected) + 1
            selected.append(output)

    summary = {
        "report_end": report_end.isoformat(),
        "candidate_window": {"start": candidate_start.isoformat(), "end": report_end.isoformat()},
        "heat_window": {"start": fresh_start.isoformat(), "end": report_end.isoformat()},
        "requested": {"total": limit, "weekly_hot": hot_target, "fresh_exploration": exploration_target},
        "selected": {
            "total": len(selected),
            "weekly_hot": len(selected_hot),
            "fresh_exploration": len(selected_exploration),
            "quota_backfill": len(backfill),
        },
        "eligible_candidates": len(eligible),
    }
    return selected, summary


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            candidates.append(value)
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Candidate paper JSONL")
    parser.add_argument("--output", type=Path, default=Path("selected-papers.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("paper-portfolio-summary.json"))
    parser.add_argument("--report-end", type=date.fromisoformat, required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--candidate-days", type=int, default=30)
    parser.add_argument("--fresh-days", type=int, default=7)
    parser.add_argument("--hot-ratio", type=float, default=0.7)
    parser.add_argument("--min-heat-score", type=float, default=40.0)
    parser.add_argument("--min-independent-signals", type=int, default=2)
    args = parser.parse_args()

    if args.limit < 1 or args.candidate_days < 1 or args.fresh_days < 1:
        parser.error("--limit and window sizes must be positive")
    if not 0.0 <= args.hot_ratio <= 1.0:
        parser.error("--hot-ratio must be between 0 and 1")

    selected, summary = select_portfolio(
        load_jsonl(args.input),
        report_end=args.report_end,
        limit=args.limit,
        candidate_days=args.candidate_days,
        fresh_days=args.fresh_days,
        hot_ratio=args.hot_ratio,
        min_heat_score=args.min_heat_score,
        min_independent_signals=args.min_independent_signals,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for item in selected:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Selected {summary['selected']['total']} papers: "
        f"{summary['selected']['weekly_hot']} weekly-hot, "
        f"{summary['selected']['fresh_exploration']} fresh-exploration, "
        f"{summary['selected']['quota_backfill']} backfill."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

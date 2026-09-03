# Report Data Schema

Use `scripts/render_report.py` after report content is normalized. JSON is always supported; YAML is accepted when PyYAML is installed. The renderer escapes all source-derived text and generates every repeated structure. Raw HTML and direct template editing are not supported; extend the schema and renderer when a new layout is required.

## Top-level shape

```json
{
  "meta": {
    "title": "AI Research Radar",
    "date_range": "2026-08-27 — 2026-09-02",
    "report_end": "2026-09-02",
    "issue_number": "001",
    "generated_at": "2026-09-03 09:00 CST",
    "deck": "One-line framing",
    "candidate_count": 52,
    "retained_count": 15,
    "executive_judgment": "Three to five sentences."
  },
  "priority_watch": [],
  "top_signals": [],
  "paper_portfolio": {},
  "axes": {},
  "synthesis": [],
  "random_signal": {},
  "research_queue": [],
  "source_health": [],
  "coverage_gaps": [],
  "registry_changes": []
}
```

## Repeated records

- `priority_watch`: one record per mandatory source with `source_id`, `name`, `organization`, `state`, `checked_at`, and optional `updates`. An update has `title`, `url`, `date`, `source`, `implication`, and optional `primary: true`. An inaccessible record also uses `failure` and `fallback`.
- `top_signals`: 1-5 records with `axis`, `score`, `confidence`, `title`, `change`, `impact`, `evidence`, `action`, and `url`.
- `paper_portfolio`: optional `candidate_window`, `heat_window`, `requested_hot`, `requested_fresh`, `selected_hot`, `selected_fresh`, and `backfill`.
- `axes.framework`: `status` plus `studies`. Each study uses `type`, `source_ids`, `confidence`, `title`, `question`, `mechanism`, `comparison`, and `sources`; each source has `label`, `url`, and `evidence_type`.
- `axes.evaluation`, `axes.evolution`, and `axes.product`: `status` plus `items`. Ordinary items use `title`, `body`, and `url`. Paper items additionally use `paper_pool`, `heat_score`, and `relevance_score`.
- `synthesis`: zero or more `relation`, `title`, `body` records.
- `random_signal`: `seed`, `title`, `tension`, `evidence`, plus optional `source_url` and `discussion_url`. Omit both URLs when no accessible eligible HN item exists; the renderer emits an explicit empty state.
- `research_queue`: `type`, `artifact`, and `outcome` records.
- `source_health`: extra non-priority failures with `source_id`, `name`, `failure`, `fallback`, and optional `checked_at`. Inaccessible priority records are inserted automatically.
- `coverage_gaps` and `registry_changes`: strings or lists of strings.

All content must use the structured fields above. Unknown presentation needs require a renderer/schema change so they remain reproducible and testable.

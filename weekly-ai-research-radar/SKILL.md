---
name: weekly-ai-research-radar
description: "Build a personalized weekly AI research brief from public, no-key sources for agent frameworks, evaluation and token economics, AI self-evolution, and AI products. Use when scanning the last week, investigating one of these themes, maintaining the source registry, or converting new AI information into research decisions; do not use for generic daily news summaries."
---

# Weekly AI Research Radar

Produce a research instrument, not a news digest. Optimize for changes that could revise the user's models, engineering choices, experiments, or writing agenda.

## Modes

Infer the mode from the request. If unclear, default to `weekly-scan` for the previous 7 complete days in Asia/Shanghai.

- `weekly-scan`: collect, rank, verify, and synthesize one weekly brief.
- `topic-scan`: search one research question without forcing broad weekly coverage.
- `source-review`: add, grade, pause, or remove sources.
- `intake`: evaluate user-provided links or notes through the same scoring system.

Load references only when their decisions become relevant:

- Before setting scope or checking mandatory sources, read [references/research-profile.md](references/research-profile.md) and [references/priority-watch.md](references/priority-watch.md).
- Before scanning or changing the registry, read [references/source-policy.md](references/source-policy.md).
- Before gap search, read [references/query-playbook.md](references/query-playbook.md).
- Before ranking or selecting papers, read [references/scoring-and-output.md](references/scoring-and-output.md).
- Before rendering or validating HTML, read [references/html-output.md](references/html-output.md) and, when using the renderer, [references/report-data-schema.md](references/report-data-schema.md).

Do not preload references for phases the request does not need.

## Operating Constraints

- Prefer sources available without API keys, login, paid subscriptions, or private credentials.
- Use first-party pages, public RSS/Atom, public GitHub repositories and release pages, arXiv/OpenReview pages, conference proceedings, and ordinary web search.
- Do not request or invent an API key. Do not treat an unauthenticated JSON endpoint as a required dependency when a public page or feed is available.
- Do not bypass paywalls, robots controls, CAPTCHAs, rate limits, or access restrictions. Record the inaccessible item and seek a primary-source alternative.
- Treat social posts, aggregators, newsletters, and community discussions as discovery leads. Promote their claims only after finding a primary source or explicitly label them as unverified signals.
- Preserve publication date and event date separately. Include an older item only when it became materially relevant during the scan window, and explain why.
- Keep factual extraction separate from interpretation. Cite the public page supporting each consequential claim.
- This is an automation-only workflow. Do not ask a person to browse a failed source, save page HTML, hand-edit JSONL, fill template placeholders, or repair generated HTML. Every stage must emit structured output or a machine-readable failure state.
- Flexibility belongs in configuration and adapters: registry URLs, parser strategies, query families, retry policy, and optional automated sources may vary without creating a manual branch.

## Weekly Scan

Treat this as a dependency graph, not a rigid serial checklist. Execute collection, normalization, selection, rendering, and validation through scripts or callable tools. There is no manual completion path.

1. Set the interval and active priorities. Use the prior 7 complete days unless the user specifies dates. State the exact inclusive date range.
2. Start these collection lanes together when tools or agents permit:
   - **Priority lane:** read [data/priority-watchlist.csv](data/priority-watchlist.csv). Fetch its RSS/Atom sources with `scripts/fetch_public_feeds.py` and its `page` sources with `scripts/fetch_page_sources.py`. Page checks may continue in the background; they do not block the other lanes.
   - **Registry lane:** scan remaining active `core` sources, then relevant `specialist` sources. Sample `weak-signal` sources only when capacity remains or triangulation needs them.
   - **Discovery lane:** run gap queries through callable search tools and collect the 30-day paper window. `scripts/collect_paper_signals.py` creates selector-ready JSONL from public arXiv and attention pages. Any additional collector must emit the same structured fields; do not assemble candidates by hand.
3. Merge lane results as they arrive. Complete every mandatory priority check before final ranking and delivery, assigning each source exactly one of `material-update`, `no-material-update`, or `inaccessible`. Record its newest relevant item and exact date. Keep inaccessible results out of `Priority Watch` and route them to `Source Health`.
4. Search unresolved gaps using the query playbook. Scan paper frontiers by mechanism rather than standing title queries. Use at least two distinct query families for each active axis unless the user narrowed the scope.
5. Normalize candidates with: title, canonical paper ID, URL, source, source tier, published date, event date if different, axis, artifact type, factual change, evidence, possible research impact, relevance score, and observed paper-heat signals. Never manufacture missing metrics.
6. Deduplicate by canonical artifact or event, apply hard gates, then rank. For papers, run `scripts/select_paper_portfolio.py`; its default target is 70% `weekly-hot` plus 30% `fresh-exploration`, with explicit backfill when a pool is short.
7. Deep-read the highest-ranked items against primary artifacts. Reduce confidence when only abstracts or secondary accounts are available. Build Agent Framework from the external comparison pool; Priority Watch may be context but cannot be its only evidence.
8. Collect Hacker News separately and run `scripts/select_random_signal.py`. Permit at most one redraw for access or safety failure, not merely because the result is surprising.
9. Stop when additional scanning mostly yields duplicates or low scores, or at the weekly budget: 40-80 candidates, 12-20 retained items, 8-12 deep reads, and 3-5 long-term knowledge candidates. Mandatory checks must still be accounted for, but a slow page should not idle independent work.
10. Render the standalone report only through `scripts/render_report.py report-data.json --output ...`. Do not edit the template or generated report by hand. The renderer invokes `scripts/validate_html_report.py`; a validation failure returns to structured data generation or renderer code, not HTML patching.

Recommended concurrency: launch the Priority, Registry, and Discovery lanes together; begin deduplication and scoring once any lane has enough results; wait only at merge points that truly require complete inputs. If delegation is unavailable, interleave network-bound fetches and local normalization rather than enforcing the numbered order literally.

For the default paper portfolio:

```powershell
python scripts/select_paper_portfolio.py paper-candidates.jsonl --report-end YYYY-MM-DD --output selected-papers.jsonl --summary paper-portfolio-summary.json
```

The selector accepts public observations under `heat_signals`: `hf_weekly_rank`, `hf_upvotes_7d`, `independent_sources_7d`, `github_weekly_trending`, `github_stars_7d`, `academic_discussions_7d`, `attention_events_7d`, and `attention_events_previous_7d`. A paper needs at least two independent signals and a heat score of 40 to enter `weekly-hot`. Papers not selected there may enter `fresh-exploration` only when published in the final 7-day window. If either pool is short, keep the report useful through explicitly labeled `quota-backfill`; report the actual mix instead of claiming 70/30.

For a feed-based Hacker News draw:

```powershell
python scripts/fetch_public_feeds.py --source hacker-news --tiers weak-signal --output hn-candidates.jsonl
python scripts/select_random_signal.py hn-candidates.jsonl --seed YYYY-MM-DD
```

For page-based registry sources:

```powershell
python scripts/fetch_page_sources.py --source claude-blog --source anthropic-research --output page-candidates.jsonl
```

For a selector-ready public paper candidate file:

```powershell
python scripts/collect_paper_signals.py --report-end YYYY-MM-DD --output paper-candidates.jsonl
python scripts/select_paper_portfolio.py paper-candidates.jsonl --report-end YYYY-MM-DD --output selected-papers.jsonl --summary paper-portfolio-summary.json
```

## Source Review

Use the registry schema in [references/source-policy.md](references/source-policy.md). A proposed source enters as `trial`, becomes `core` or `specialist` only after repeated high-value yields, and is paused after sustained low yield. Keep the standing registry at 50-70 sources; the starter registry is intentionally smaller and should grow from observed value.

When changing the registry, run:

```powershell
python scripts/validate_registry.py data/source-registry.csv
python scripts/validate_watchlist.py data/priority-watchlist.csv data/source-registry.csv
```

## Failure Handling

- If a feed fails, automatically try the registered official index or release-page adapter and mark `feed_health=degraded`; do not silently substitute a third-party mirror.
- If an automated collector still fails, write its error record, mark the source `inaccessible`, and continue independent lanes. Do not request human inspection or fabricate the missing result.
- If search results conflict, report the disagreement and prefer the artifact closest to the claim.
- If fewer than three valuable developments exist, return a quiet-week brief with the searches performed and the most important non-events or continuing signals.
- If the user requests automation, keep this Skill as the reasoning layer and schedule invocation separately; do not embed credentials or notification secrets here.

## Output Contract

Return a Chinese brief unless the user requests another language. The default deliverable is a validated standalone `.html` report; provide Markdown or plain text only when the user explicitly requests it. Include:

1. Exact scan interval and a 3-5 sentence executive judgment.
2. `Priority Watch`: summarize accessible mandatory sources by organization: Anthropic, OpenAI, Hermes, Pi, DeepSeek Harness, Agno, LangChain, and Langfuse. Show at most one primary article per organization. Represent other qualifying updates as a count plus at most three short title links, with a no-JavaScript `查看全部` popover containing every additional update. Do not display `inaccessible` sources here.
3. `Top signals`: at most five items, each with what changed, why it matters to the user's research, evidence, confidence, and recommended action.
4. Coverage by active research axis, including `no material signal` where appropriate. Render Agent Framework as an external-comparison and mechanism-research layer with at most three research notes; each note must identify its source set and link every consequential evidence artifact.
5. Cross-signal synthesis: tensions, convergences, or causal links across at least two items. Omit this section when no defensible connection exists.
6. `Random signal`: exactly one Hacker News-derived item, clearly separated from ranked research signals, with its connection or productive tension stated. If no accessible eligible item exists, say so rather than substituting another source.
7. `Research queue`: 3-5 items classified as read, reproduce, compare, write, or watch.
8. Source-health notes: every inaccessible priority source with failure reason and official fallback attempted, other inaccessible core sources, important blind spots, and registry changes worth considering.

Do not produce a link dump, generic trend language, unsupported predictions, or a fixed number of items independent of quality.

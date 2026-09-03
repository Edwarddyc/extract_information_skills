# Priority Watch

The sources in `data/priority-watchlist.csv` are mandatory weekly checks. This list overrides ordinary tier coverage, but not execution concurrency: start all checks early and finish every row before final ranking and delivery. Feed-backed results may flow into gap search, paper discovery, and source scanning while slower page checks continue in parallel.

## Required State

Record exactly one weekly state for every watchlist source:

- `material-update`: at least one change in the interval can affect a research model, architecture, evaluation, experiment, or product decision.
- `no-material-update`: the source was checked, but there was no qualifying change in the interval. Record the newest visible item and its date when available.
- `inaccessible`: the source could not be checked. Record the failure and the official fallback attempted.

Do not use `no-material-update` merely because an item scored below Top Signals. Briefly note the new item when it changes the ecosystem but is too small for deeper analysis.

## Observation Order

The order below defines review and reporting precedence, not a blocking fetch sequence. Preserve it when resolving duplicates and writing the final coverage record; fetch independent sources concurrently when possible.

### 1. Anthropic

Check Claude Blog and Anthropic Research separately. Claude Blog is the product and agent-engineering surface; Anthropic Research is the research surface. Do not let the same announcement count twice.

### 2. OpenAI

Check OpenAI Engineering, OpenAI Research, and the OpenAI News feed. Engineering has priority for agent loops, harness engineering, sandboxes, context management, skills, inference infrastructure, and production lessons. Research has priority for evaluations, reasoning, self-improvement, and empirical results. Use the broad feed as a completeness check, then deduplicate against the filtered indexes.

### 3. Hermes, Pi, and DeepSeek Harness

Check Hermes, Pi, and DeepSeek Harness. Focus on runtime architecture, agent loop behavior, context and state, tools, memory, plugin systems, lifecycle, recovery, and breaking changes.

For release feeds, compare the latest qualifying release with the previous release. For DeepSeek Harness's commit feed, cluster commits by subsystem and report only architectural, behavioral, or compatibility consequences.

Treat Hermes, Pi, and DeepSeek Harness as three separate report organizations even though they share a harness-oriented research lens.

### 4. Agno and LangChain

Check Agno and the LangChain family: LangChain releases, LangGraph releases, and the LangChain engineering blog. Collapse repetitive package patches into one change narrative. Distinguish framework capability, deployment/product announcements, and compatibility maintenance.

Report Agno separately. Consolidate LangChain, LangGraph, and the LangChain engineering blog into one LangChain organization module.

### 5. Langfuse

Check Langfuse releases and blog. Observe changes in tracing semantics, trajectory inspection, evaluation, datasets, cost and latency accounting, experiments, MCP/CLI access, production debugging, and agent-specific observability. Translate feature releases into implications for harness design and evaluation methodology.

## Reporting

The HTML report must include a `Priority Watch` section before ranked Top Signals. Consolidate accessible source checks into organization modules for Anthropic, OpenAI, Hermes, Pi, DeepSeek Harness, Agno, LangChain, and Langfuse. Keep the thematic `group` column for collection order only; do not use it as the report layout.

Each organization module has one visual hierarchy:

1. Show the organization name, aggregate weekly state, and latest checked date.
2. When material updates exist, select exactly one primary article or release by research impact, not recency alone. Give it the only headline-sized treatment in the module, one short implication, and its primary link.
3. Show the number of other qualifying updates after excluding the primary item. List at most three of their titles as compact links; use the count to preserve completeness when more exist. When this count is greater than zero, place a `查看全部 N 项` control beside it. The control opens a small native popover containing every additional update with title, date, source label, and primary link. Do not summarize each secondary item.
4. When there is no material update, show a compact `no-material-update` statement with zero additional updates and no primary article.

A primary item may also appear in Top Signals; link rather than repeat the full analysis.

Do not display an `inaccessible` source in `Priority Watch`, including in an organization's source metadata. Move it to the final `Source Health` section and show it exactly once with the source name, failure reason, check date, and official fallback attempted. If an organization still has another accessible source, keep its module and attach only the accessible source IDs. If all its sources are inaccessible, omit the organization module. The combined `Priority Watch` and `Source Health` sections must account for every mandatory source exactly once.

Priority coverage is not a quota for positive news. A complete week may contain many `no-material-update` states.

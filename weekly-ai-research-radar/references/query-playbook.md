# Query Playbook

Construct searches from `entity + change term + date constraint`, then add a mechanism or evidence term. Prefer official domains and repositories.

## Framework Engineering

Use an external comparison pool: PydanticAI, Google ADK, Microsoft Agent Framework, OpenHands, Letta Code, A2A, OpenTelemetry GenAI semantic conventions, MCP specification, and trial source Strands Agents. Do not use Priority Watch entities as the starting set for this axis.

Research question families:

- `(agent runtime OR harness) (state OR lifecycle OR recovery) implementation comparison`
- `(sandbox OR workspace OR code execution) agent isolation failure architecture`
- `(durable workflow OR session replay OR checkpoint) agent runtime semantics`
- `(agent memory OR context repository) consistency concurrency compaction`
- `(A2A OR MCP OR agent protocol) interoperability state security`
- `(OpenTelemetry OR tracing) agent workflow plan tool causal semantics`

For each candidate question, inspect release notes plus at least one deeper artifact: architecture documentation, code, tests, specification diff, issue, or benchmark. Form a note only when the evidence supports a mechanism finding or a meaningful contrast. AutoGen and Semantic Kernel are historical comparison material; use Microsoft Agent Framework for current Microsoft changes.

Stop after three defensible research notes. Prefer one runtime/harness mechanism, one cross-framework comparison, and one protocol/observability or failure-analysis note. If the evidence remains a list of features, omit it from the axis.

## Paper Frontier Scan

Use two clocks rather than sorting the previous week's arXiv results by publication time:

- Candidate window: papers first published or materially revised in the 30 inclusive days ending on the report date.
- Heat window: public attention observed in the final 7 inclusive days.

Build two pools. Allocate 70% of the paper portfolio to `weekly-hot` and 30% to `fresh-exploration`. The hot pool may contain a delayed breakout from earlier in the 30-day window; the exploration pool must have been published or materially revised inside the 7-day heat window.

Start hot-paper discovery with Hugging Face Weekly Trending. Confirm the canonical paper on arXiv, OpenReview, or proceedings, then look for independent recurrence and the official code artifact. GitHub Weekly Trending, public OpenReview activity, and multiple independent technical sources are supporting attention signals. Total stars, cumulative citations, an author's own launch posts, and Hacker News points do not by themselves establish weekly heat. Hacker News remains reserved for the Random Signal slot.

Record only observed values. Do not estimate vote deltas, star growth, discussion counts, or previous-week attention from snippets. A paper needs at least two independent heat signals before entering the high-heat pool.

Scan recent paper indexes by research problem and mechanism, not by the title of a known paper. Do not add a standing query for one paper unless the user explicitly asks to track it.

Priority 1, agent self-evolution:

- `(self-improving OR self-evolving OR recursive improvement) agent`
- `(self-play OR curriculum generation OR experience consolidation) language agent`
- `(reflection OR self-repair OR self-debugging) agent empirical evaluation`
- `(memory evolution OR skill acquisition OR lifelong learning) LLM agent`

Priority 2, harness and runtime learning:

- `(agent harness OR runtime harness OR execution scaffold) learning evaluation`
- `(external state OR workspace OR context management) long-horizon agent`
- `(tool policy OR harness policy OR runtime control) agent`
- `(trajectory compression OR progress tracking OR experience reuse) agent`

Priority 3, reinforcement learning frontiers:

- `(reinforcement learning OR RL) tool-using agent long horizon`
- `(process reward OR outcome reward OR verifier) agent training`
- `(offline RL OR online RL OR policy optimization) language agent`
- `(test-time learning OR inference-time learning) agent`

For each family, compare mechanisms, task settings, reward construction, training cost, token/runtime cost, ablations, and released code. Search adjacent terminology once to avoid vocabulary lock-in. Assign `relevance_score` with the normal research rubric, collect heat observations separately, then run `scripts/select_paper_portfolio.py`. A paper should enter the report because it survives the relevance and evidence gates, not because its name was preconfigured or it was popular on one platform.

## Evaluation and Token Economics

Query families:

- `(agent evaluation OR agent benchmark) trajectory tool use cost`
- `(inference-time compute OR test-time scaling OR token budget) agent`
- `(LLM judge OR judge reliability) bias contamination calibration`
- `(multi-agent OR self-consistency) token cost efficiency ablation`

Useful artifact terms: paper, dataset, benchmark, leaderboard, repository, ablation, cost, latency, tokens, failure, replication.

## Self-Evolution and AGI Philosophy

Query families:

- `(self-improving agent OR recursive self-improvement OR self-play agent) empirical`
- `(intrinsic motivation OR emotion mechanism OR persistent identity) language agent`
- `(autonomous research agent OR curriculum generation) evaluation`
- `(agency OR autonomy OR self-model) artificial intelligence paper`

Require at least one mechanism/evidence query for every philosophy-oriented query.

These queries complement the paper frontier scan. Use this section for broader conceptual work; use the frontier scan for recent empirical papers.

## Hacker News Serendipity

Use Hacker News only for the report's random signal slot. Collect from its public RSS or public pages without login. Exclude job posts, pure political commentary, and items inaccessible without authentication. Keep broadly adjacent engineering, science, AI, developer-tool, systems, or market signals even when they fall just outside the four main axes.

Do not rank Hacker News popularity as research evidence. Open the submitted page, identify the primary artifact when possible, and label the result `random signal`. If it contains a consequential claim, verify it normally or describe it as an unverified lead.

## Products and Platforms

Query families:

- `(AI research workspace OR intelligence analysis AI OR document agent) launch architecture`
- `(AI-native content workflow OR content strategy agent) case study evaluation`
- `site:<official-domain> changelog agent workflow provenance evaluation`
- `<product> release notes pricing limits integrations`

## Gap Search

After initial collection, search explicitly for:

- criticism or failed replication of the week's strongest claim;
- code or data corresponding to a paper;
- benchmark methodology behind a claimed improvement;
- cost, token, latency, and failure information omitted from announcements;
- related work that predates a purportedly new mechanism.

Stop a query family after two result pages or equivalent yield no new qualifying artifact. Reformulate once; then record the gap instead of searching indefinitely.

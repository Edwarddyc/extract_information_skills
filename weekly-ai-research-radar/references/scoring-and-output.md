# Scoring and Output

## Hard Gates

Reject an item when any applies:

- no material change, artifact, argument, result, or observed event;
- outside the active research profile;
- duplicate of a stronger retained item;
- consequential claim has neither primary evidence nor an explicit `unverified signal` label;
- publication/event date cannot be placed relative to the scan interval;
- primarily promotional and reveals no transferable mechanism, evidence, or workflow.

## Score

Score retained candidates out of 100:

| Dimension | Max | Question |
|---|---:|---|
| Personal relevance | 25 | Can it alter a current research model, system, experiment, or document? |
| Novelty | 15 | Is the mechanism, evidence, or contradiction genuinely new to this research map? |
| Evidence strength | 20 | Is there a primary artifact, method detail, baseline, data, or reproducible code? |
| Strategic consequence | 15 | Could it change a medium-term research direction or architecture choice? |
| Actionability | 15 | Is there a clear read, reproduce, compare, write, or watch action? |
| Freshness | 5 | Did the substantive event occur in the interval? |
| Cross-axis value | 5 | Does it connect at least two research axes non-trivially? |

Penalties:

- subtract 10 for a major undisclosed conflict of interest or purely self-reported comparison;
- subtract 10 when the full artifact is inaccessible and only an abstract/snippet is available;
- subtract 5-20 for missing baselines, cost data, or methodology when central to the claim;
- cap at 59 for an unverified signal.

Ranking bands:

- 80-100: top signal and likely deep read.
- 65-79: retain in axis section.
- 50-64: watchlist only if strategically unusual.
- below 50: omit from report.

Confidence is separate from score: `high`, `medium`, or `low`. A highly relevant rumor may score 59 but still have low confidence.

## Paper Portfolio

Paper heat is a discovery and attention-allocation score; it does not replace the research score above. Keep both values visible internally and never describe popularity as evidence quality.

Use a 30-day candidate window and a 7-day heat window. The default ten-paper portfolio requests seven `weekly-hot` papers and three `fresh-exploration` papers. For other portfolio sizes, `scripts/select_paper_portfolio.py` rounds to the nearest achievable 70/30 allocation.

Heat score components total 100:

| Public observation | Max | Interpretation |
|---|---:|---|
| Hugging Face weekly rank and observed 7-day upvotes | 35 | Direct paper-level attention |
| Independent-source recurrence | 25 | Cross-community propagation |
| GitHub weekly trend or observed 7-day stars | 20 | Artifact adoption momentum |
| Public academic discussion in the heat window | 10 | Research-community engagement |
| Attention acceleration over the previous 7 days | 10 | Rising rather than accumulated attention |

Require heat score 40 and at least two independent signals for `weekly-hot`. Keep cumulative citations out of weekly heat. Treat unavailable observations as zero, not as negative evidence. When one pool lacks enough qualified papers, label replacements `quota-backfill` and report the requested and actual counts.

## Candidate Card

Use this internal shape:

```yaml
title: ""
url: ""
source: ""
source_tier: "core|specialist|weak-signal|trial"
published_date: "YYYY-MM-DD"
event_date: "YYYY-MM-DD|unknown"
axes: []
artifact_type: "paper|code|release|docs|benchmark|analysis|discussion|product"
factual_change: ""
evidence: ""
research_impact: ""
score: 0
confidence: "high|medium|low"
action: "read|reproduce|compare|write|watch|none"
relevance_score: 0
paper_pool: "weekly-hot|fresh-exploration|quota-backfill|not-applicable"
heat_score: 0
heat_signal_count: 0
```

## Weekly Report Template

```markdown
# AI Research Radar · YYYY-MM-DD to YYYY-MM-DD

## 本周判断
3-5 句：真正改变了什么，哪些方向没有实质变化，本周研究注意力应投向哪里。

## 重点观察

按 Anthropic、OpenAI、Hermes、Pi、DeepSeek Harness、Agno、LangChain、Langfuse 分成机构模块。每个机构只突出一篇最重要文章或发布，其余更新显示总数并最多列出三个标题链接；`inaccessible` 来源不在此展示，统一移至报告末尾的 Source Health。

## Top Signals

### 1. 结论式标题 `[score/100 · confidence]`
- 发生了什么：
- 为什么与你有关：
- 证据与限制：
- 建议动作：
- 来源：

所有 Top Signal 使用完全相同的字段顺序。`发生了什么`只陈述变化，避免混入影响判断；后三个字段各自控制为一个紧凑段落，扩展分析放入对应研究轴，避免某一条信号因重复解释显著变长。

## 研究轴扫描

### Agent Framework Engineering
写 0-3 篇外部比较与机制研究笔记，或明确 `No material signal`。每篇固定包含：

- 研究问题：本周证据试图回答什么架构问题；
- 机制发现：从代码、文档、规范、测试或发布说明中观察到什么；
- 比较与边界：相对于另一实现的差异、适用条件和未知项；
- 数据来源：列出来源名称、证据类型、日期和可点击原始链接。

Priority Watch 项目只能作为比较对象，不能作为唯一证据。不要复述其更新摘要。跨框架研究至少使用两个外部来源；单项目机制深读至少使用同一来源的两类一手材料。

### Evaluation / Token Economics
...

### Self-Evolution / AGI
...

### AI Products / Platforms
...

## 交叉洞察
只写由至少两个已核验信号支持的连接、张力或因果假设。

## Random Signal · Hacker News
- 随机抽中的信号：
- 它为何值得扰动当前研究视野：
- 已核验事实与未知项：
- 原始提交与讨论：

## Research Queue
| Priority | Action | Artifact | Intended output |
|---:|---|---|---|

## Source Health
逐一列出 Priority Watch 中所有 `inaccessible` 来源、失败原因与官方替代入口检查结果，再记录其他失效核心源、覆盖盲点及建议新增/降级/暂停的来源。
```

Use concise synthesis. Do not repeat the same summary in the top signals and axis sections; axis sections should add technical detail or comparison.

The Hacker News random signal is exempt from the score threshold and must not appear in `Top Signals` solely because it was selected. Apply ordinary evidence and confidence labels, and omit it only when no eligible accessible item exists.

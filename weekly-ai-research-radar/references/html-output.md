# HTML Output

Generate the final weekly brief as a standalone HTML file based on [../assets/weekly-report-template.html](../assets/weekly-report-template.html). The visual language is editorial and restrained: warm paper background, near-black text, serif analytical headlines, sans-serif metadata, thin rules, flat sections, and one muted coral accent. Do not copy Claude branding, logos, proprietary fonts, text, or imagery.

## Rendering Procedure

1. Run `python scripts/render_report.py report-data.json --output reports/ai-radar-YYYY-MM-DD.html`; read [report-data-schema.md](report-data-schema.md) for its structured input. This is the only supported report-generation path.
2. The renderer escapes source-derived fields, creates repeated blocks, assigns unique popover IDs, and invokes the validator by default. Do not copy-edit the template, inject raw HTML fragments, or patch the generated report.
3. Match repeated signal, axis-item, synthesis, and queue blocks to actual content. Keep at most five Top Signals and never add filler.
4. Fill `PAPER_PORTFOLIO_SUMMARY_HTML` with the exact 30-day candidate window, 7-day heat window, requested 70/30 counts, and actual selected counts from `paper-portfolio-summary.json`. When no paper survives, state that plainly. Do not imply the requested ratio was achieved when backfill occurred.
5. For a quiet research axis, set its status to `No material signal` and render one short `.axis-item` explaining what was checked and why no item crossed the threshold. Agent Framework is the exception: render zero to three `.framework-study` notes using `FRAMEWORK_STUDIES_HTML`; when quiet, render one `.framework-empty` explanation instead.
6. Account for all 14 mandatory sources exactly once across `Priority Watch` and `Source Health`. Consolidate accessible sources into `.watch-org` modules using the organization mapping in `data/priority-watchlist.csv`; put their comma-separated IDs in `data-source-ids`. Render inaccessible sources individually in `CORE_SOURCE_HEALTH_HTML` with `data-location="source-health"` and state `inaccessible`.
7. Preserve the template's CSS classes and section order unless the user explicitly asks for a structural change.
8. Keep the file self-contained. Do not add external fonts, JavaScript, trackers, remote stylesheets, base64 decorations, or copied Claude assets. Ordinary source links may remain remote.
9. Use semantic HTML, real links, ISO dates in `datetime`, meaningful headings, and concise link labels.
10. Escape `&`, `<`, `>`, and quotes in all source-derived text before insertion. Never paste raw article HTML into the report.

## Top Signal Structure

Render Top Signals as one full-width ranked row per item, never as unequal cards. Preserve the same field order in every row: rank and metadata, conclusion-style title, `发生了什么`, then the three aligned fields `为什么与你有关`, `证据与限制`, and `建议动作`, followed by one primary-source link. Keep field content concise enough to scan; move extended technical discussion to the relevant research-axis section. Render `发生了什么` as the single deep-ink contrast band within each signal; do not add separate status legends or status modules.

Use exactly one `.signal-number`, `.signal-meta`, `.signal-change`, and `.signal-source` per `.signal`, with exactly three `.signal-field` elements. Keep at most five signal rows. The template exposes one `TOP_SIGNALS_HTML` placeholder; the renderer produces the rows from `top_signals`.

Priority organization fragment:

```html
<article class="watch-org" data-organization="anthropic"
  data-source-ids="claude-blog,anthropic-research"
  data-state="material-update" data-location="priority-watch" data-additional-count="4">
  <header class="watch-org-head">
    <h3>Anthropic</h3>
    <time datetime="2026-08-29">2026-08-29</time>
  </header>
  <div class="watch-primary-block">
    <p class="watch-label">本周最重要</p>
    <h4><a class="watch-primary" href="https://claude.com/blog/example">主文章标题</a></h4>
    <p>一句话说明它对当前研究的意义。</p>
  </div>
  <div class="watch-more">
    <div class="watch-more-head">
      <p><strong>另有 4 项更新</strong></p>
      <button class="watch-all-trigger" type="button" popovertarget="updates-anthropic">查看全部 4 项</button>
    </div>
    <ul>
      <li><a class="watch-secondary" href="https://www.anthropic.com/research/example">次要更新标题</a></li>
    </ul>
    <div class="watch-popover" id="updates-anthropic" popover>
      <header class="watch-popover-head">
        <h4>Anthropic · 其他 4 项更新</h4>
        <button class="watch-popover-close" type="button" popovertarget="updates-anthropic"
          popovertargetaction="hide" aria-label="关闭全部更新" title="关闭">×</button>
      </header>
      <ol class="watch-all-list">
        <li class="watch-all-item">
          <a class="watch-all-link" href="https://www.anthropic.com/research/example">完整更新标题</a>
          <time datetime="2026-08-28">2026-08-28</time>
          <span class="watch-all-source">Anthropic Research</span>
        </li>
        <!-- Continue until all four additional updates are represented. -->
      </ol>
    </div>
  </div>
</article>
```

Use exactly one `.watch-primary` link for a `material-update` module and none for a `no-material-update` module. `data-additional-count` counts all qualifying updates after excluding the primary item; list zero to three secondary title links regardless of the count. When the count is positive, include exactly one `.watch-all-trigger` and one `.watch-popover`, with exactly `data-additional-count` `.watch-all-item` rows. The button's `popovertarget`, popover `id`, and close button target must match and be unique across the document. Do not add JavaScript: native popovers provide opening, light dismissal, and Escape handling. When the count is zero, omit the trigger and popover. Use the single placeholder `PRIORITY_ORGANIZATIONS_HTML` for all organization modules in this order: Anthropic, OpenAI, Hermes, Pi, DeepSeek Harness, Agno, LangChain, Langfuse.

Inaccessible priority-source fragment, rendered only in `Source Health`:

```html
<article class="health-source" data-source-id="claude-blog" data-state="inaccessible" data-location="source-health">
  <h4>Claude Blog</h4>
  <p>2026-08-29 检查失败：说明失败原因。已尝试官方 RSS 或官方索引页，说明替代检查结果。</p>
</article>
```

Axis item fragment:

```html
<article class="axis-item">
  <h4>结论式标题</h4>
  <p>技术细节、比较或限制。</p>
  <a href="https://primary-source.example">原始来源 →</a>
</article>
```

For a retained paper, add its pool and both scores without changing the analytical body:

```html
<article class="axis-item paper-item" data-paper-pool="weekly-hot"
  data-heat-score="82" data-relevance-score="91">
  <div class="paper-selection-meta">
    <span class="paper-pool paper-pool-hot">本周高热</span>
    <span>Heat 82 · Research fit 91</span>
  </div>
  <h4>结论式论文标题</h4>
  <p>机制、证据、限制以及它与当前研究问题的关系。</p>
  <a href="https://arxiv.org/abs/example">原始论文 →</a>
</article>
```

Allowed `data-paper-pool` values are `weekly-hot`, `fresh-exploration`, and `quota-backfill`. Use visible labels `本周高热`, `最新探索`, and `配额回填`. Heat score is attention, while Research fit is the ordinary research score; do not combine them into a single number.

Agent Framework research-note fragment:

```html
<article class="framework-study" data-study-type="cross-framework"
  data-source-ids="pydantic-ai,google-adk">
  <p class="study-meta">Research note 01 · high confidence</p>
  <h4>结论式研究标题</h4>
  <dl class="study-findings">
    <div class="study-question"><dt>研究问题</dt><dd>要检验的架构问题。</dd></div>
    <div class="study-mechanism"><dt>机制发现</dt><dd>由一手材料支持的机制说明。</dd></div>
    <div class="study-comparison"><dt>比较与边界</dt><dd>实现差异、适用条件与未知项。</dd></div>
  </dl>
  <footer class="study-sources">
    <p>数据来源</p>
    <ol>
      <li><a class="study-source" data-evidence-type="release"
        href="https://github.com/pydantic/pydantic-ai/releases">PydanticAI release notes</a></li>
      <li><a class="study-source" data-evidence-type="docs"
        href="https://google.github.io/adk-docs/">Google ADK architecture docs</a></li>
    </ol>
  </footer>
</article>
```

Allowed `data-study-type` values are `cross-framework`, `mechanism`, `standard`, and `failure-analysis`. Allowed source IDs are `pydantic-ai`, `google-adk`, `microsoft-agent-framework`, `openhands`, `letta-code`, `a2a-spec`, `otel-genai-semconv`, `mcp-spec`, and `strands-agents`. Each note needs at least two clickable `.study-source` links with `data-evidence-type`; a `cross-framework` note needs at least two distinct source IDs. Every declared source ID must be backed by at least one link to that source's official repository or documentation domain. Priority Watch source IDs do not count as framework-study evidence.

When no defensible note exists, use `<p class="framework-empty">No material signal：说明检查过的外部来源及证据不足之处。</p>` and render no `.framework-study`.

Queue row fragment:

```html
<tr>
  <td>01</td>
  <td>Reproduce</td>
  <td>Artifact name</td>
  <td>明确的预期产出</td>
</tr>
```

## Verification

Before delivery, run the checks automatically. A failure must update structured input or renderer/parser code and rerun the pipeline; it must not trigger hand-editing:

- run `python scripts/validate_html_report.py <report.html>`;
- confirm no `{{...}}` placeholders remain;
- inspect at approximately 1440px desktop and 390px mobile widths;
- confirm there is no horizontal page overflow, clipped title, nested card styling, or empty required section;
- confirm every consequential claim has a clickable primary source;
- confirm all mandatory source IDs appear exactly once across `Priority Watch` and `Source Health`;
- confirm every accessible source is attached to its correct organization module and inaccessible sources never appear in `data-source-ids`;
- confirm every `material-update` organization has exactly one primary link, every `no-material-update` organization has none, and secondary title links do not exceed three;
- confirm every positive additional-update count has one working native popover whose complete item count matches `data-additional-count`, and all popover IDs are unique;
- confirm Agent Framework contains no more than three research notes, every note uses only the external source pool, and every factual mechanism note exposes at least two typed primary-source links;
- confirm the Hacker News item appears only in the separate Random Signal band;
- confirm print preview remains readable and does not split individual signal blocks unnecessarily.

When browser-based verification is available, open the local report, capture desktop and mobile screenshots, and correct layout issues before delivery.

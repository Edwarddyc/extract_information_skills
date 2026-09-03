from __future__ import annotations

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_html_report.py"
TEMPLATE = ROOT / "assets" / "weekly-report-template.html"
SPEC = importlib.util.spec_from_file_location("validate_html_report", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def filled_template(
    inaccessible_source: str | None = None,
    no_material_org: str | None = None,
    framework_empty: bool = False,
    framework_study_count: int = 1,
    evaluation_html: str | None = None,
) -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    watch_organizations = {
        "anthropic": ["claude-blog", "anthropic-research"],
        "openai": ["openai-engineering", "openai-research", "openai-news"],
        "hermes": ["hermes-repo"],
        "pi": ["pi-agent"],
        "deepseek-harness": ["deepseek-harness"],
        "agno": ["agno-repo"],
        "langchain": ["langchain-repo", "langgraph-repo", "langchain-blog"],
        "langfuse": ["langfuse-repo", "langfuse-blog"],
    }

    def organization_html() -> str:
        modules: list[str] = []
        for organization, source_ids in watch_organizations.items():
            accessible = [source_id for source_id in source_ids if source_id != inaccessible_source]
            if not accessible:
                continue
            if organization == no_material_org:
                modules.append(
                    f'<article class="watch-org" data-organization="{organization}" '
                    f'data-source-ids="{",".join(accessible)}" data-state="no-material-update" '
                    f'data-location="priority-watch" data-additional-count="0">'
                    f'<header class="watch-org-head"><h3>{organization}</h3></header>'
                    f'<p>No material update.</p></article>'
                )
                continue
            popover_id = f"updates-{organization}"
            modules.append(
                f'<article class="watch-org" data-organization="{organization}" '
                f'data-source-ids="{",".join(accessible)}" data-state="material-update" '
                f'data-location="priority-watch" data-additional-count="2">'
                f'<header class="watch-org-head"><h3>{organization}</h3></header>'
                f'<a class="watch-primary" href="https://example.com/primary">Primary</a>'
                f'<a class="watch-secondary" href="https://example.com/one">One</a>'
                f'<a class="watch-secondary" href="https://example.com/two">Two</a>'
                f'<button class="watch-all-trigger" type="button" '
                f'popovertarget="{popover_id}">View all</button>'
                f'<div class="watch-popover" id="{popover_id}" popover>'
                f'<button class="watch-popover-close" type="button" '
                f'popovertarget="{popover_id}" popovertargetaction="hide">Close</button>'
                f'<li class="watch-all-item"><a class="watch-all-link" '
                f'href="https://example.com/all-one">All one</a></li>'
                f'<li class="watch-all-item"><a class="watch-all-link" '
                f'href="https://example.com/all-two">All two</a></li>'
                f'</div>'
                f'</article>'
            )
        return "".join(modules)

    def replacement(match: re.Match[str]) -> str:
        name = match.group(0)[2:-2]
        if name == "PRIORITY_ORGANIZATIONS_HTML":
            return organization_html()
        if name == "TOP_SIGNALS_HTML":
            return (
                '<article class="signal"><span class="signal-number">01</span>'
                '<div class="signal-body"><p class="signal-meta">Axis · 90/100 · high</p>'
                '<h3>Signal</h3><div class="signal-change"><p>Change</p></div><dl>'
                '<div class="signal-field"><dt>Impact</dt><dd>I</dd></div>'
                '<div class="signal-field"><dt>Evidence</dt><dd>E</dd></div>'
                '<div class="signal-field"><dt>Action</dt><dd>A</dd></div></dl>'
                '<a class="signal-source" href="https://example.com/source">Source</a>'
                '</div></article>'
            )
        if name == "SYNTHESIS_HTML":
            return '<article><span class="relation">Tension</span><h3>Finding</h3><p>Body</p></article>'
        if name == "FRAMEWORK_STUDIES_HTML":
            if framework_empty:
                return '<p class="framework-empty">No material signal.</p>'
            return "".join(
                '<article class="framework-study" data-study-type="cross-framework" '
                'data-source-ids="pydantic-ai,google-adk">'
                f'<p class="study-meta">Research note {index:02d}</p><h4>Finding</h4>'
                '<dl class="study-findings">'
                '<div class="study-question"><dt>Question</dt><dd>Q</dd></div>'
                '<div class="study-mechanism"><dt>Mechanism</dt><dd>M</dd></div>'
                '<div class="study-comparison"><dt>Comparison</dt><dd>C</dd></div>'
                '</dl><footer class="study-sources"><p>Sources</p>'
                '<a class="study-source" data-evidence-type="release" '
                'href="https://github.com/pydantic/pydantic-ai/releases">Release</a>'
                '<a class="study-source" data-evidence-type="docs" '
                'href="https://google.github.io/adk-docs/">Docs</a></footer></article>'
                for index in range(1, framework_study_count + 1)
            )
        if name == "CORE_SOURCE_HEALTH_HTML" and inaccessible_source:
            return (
                f'<article class="health-source" data-source-id="{inaccessible_source}" '
                f'data-state="inaccessible" data-location="source-health">'
                f'<h4>{inaccessible_source}</h4><p>Official fallback failed.</p></article>'
            )
        if name == "EVALUATION_ITEMS_HTML" and evaluation_html is not None:
            return evaluation_html
        if name.endswith("_URL"):
            return "https://example.com/source"
        if name.endswith("_HTML"):
            return "<p>Sample verified content.</p>"
        if name == "REPORT_END_ISO":
            return "2026-08-28"
        return "Sample content"

    return re.sub(r"\{\{[A-Z0-9_]+\}\}", replacement, text)


class HtmlReportTests(unittest.TestCase):
    def test_filled_template_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(filled_template(), encoding="utf-8")
            self.assertEqual(VALIDATOR.validate(path), [])

    def test_unresolved_template_is_rejected(self) -> None:
        errors = VALIDATOR.validate(TEMPLATE)
        self.assertTrue(any("unresolved placeholders" in error for error in errors))

    def test_missing_priority_source_is_rejected(self) -> None:
        text = filled_template().replace(
            'data-source-ids="claude-blog,anthropic-research"',
            'data-source-ids="removed,anthropic-research"',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("missing priority watch sources" in error for error in errors))

    def test_inaccessible_source_in_source_health_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(filled_template(inaccessible_source="claude-blog"), encoding="utf-8")
            self.assertEqual(VALIDATOR.validate(path), [])

    def test_inaccessible_source_in_priority_watch_is_rejected(self) -> None:
        text = filled_template().replace(
            'data-organization="anthropic" data-source-ids="claude-blog,anthropic-research" '
            'data-state="material-update"',
            'data-organization="anthropic" data-source-ids="claude-blog,anthropic-research" '
            'data-state="inaccessible"',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("wrong section" in error for error in errors))

    def test_location_label_cannot_hide_wrong_section(self) -> None:
        text = filled_template().replace(
            'data-state="material-update" data-location="priority-watch"',
            'data-state="inaccessible" data-location="source-health"',
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("wrong section" in error for error in errors))

    def test_more_than_one_primary_article_is_rejected(self) -> None:
        text = filled_template().replace(
            '<a class="watch-primary" href="https://example.com/primary">Primary</a>',
            '<a class="watch-primary" href="https://example.com/primary">Primary</a>'
            '<a class="watch-primary" href="https://example.com/second">Second</a>',
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("organization summary" in error for error in errors))

    def test_source_in_wrong_organization_is_rejected(self) -> None:
        text = filled_template().replace(
            'data-organization="anthropic"', 'data-organization="openai"', 1
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("wrong organization" in error for error in errors))

    def test_no_material_update_has_no_articles(self) -> None:
        text = filled_template(no_material_org="anthropic")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            self.assertEqual(VALIDATOR.validate(path), [])

    def test_more_than_three_secondary_links_is_rejected(self) -> None:
        text = filled_template().replace(
            'data-additional-count="2"', 'data-additional-count="4"', 1
        ).replace(
            '<a class="watch-secondary" href="https://example.com/two">Two</a>',
            '<a class="watch-secondary" href="https://example.com/two">Two</a>'
            '<a class="watch-secondary" href="https://example.com/three">Three</a>'
            '<a class="watch-secondary" href="https://example.com/four">Four</a>',
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("organization summary" in error for error in errors))

    def test_inconsistent_top_signal_structure_is_rejected(self) -> None:
        text = filled_template().replace('class="signal-change"', 'class="removed-change"', 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("Top Signal structure" in error for error in errors))

    def test_missing_complete_updates_popover_is_rejected(self) -> None:
        text = filled_template().replace('class="watch-popover"', 'class="removed-popover"', 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("organization summary" in error for error in errors))

    def test_popover_must_list_every_additional_update(self) -> None:
        text = filled_template().replace('class="watch-all-item"', 'class="removed-item"', 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("organization summary" in error for error in errors))

    def test_framework_study_requires_explicit_sources(self) -> None:
        text = filled_template().replace('class="study-source"', 'class="removed-source"', 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("Framework research note" in error for error in errors))

    def test_framework_study_rejects_priority_watch_source(self) -> None:
        text = filled_template().replace(
            'data-source-ids="pydantic-ai,google-adk"',
            'data-source-ids="pydantic-ai,hermes-repo"',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("Framework research note" in error for error in errors))

    def test_framework_empty_state_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(filled_template(framework_empty=True), encoding="utf-8")
            self.assertEqual(VALIDATOR.validate(path), [])

    def test_framework_rejects_more_than_three_notes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(filled_template(framework_study_count=4), encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("at most three" in error for error in errors))

    def test_framework_source_id_requires_matching_official_link(self) -> None:
        text = filled_template().replace(
            'href="https://google.github.io/adk-docs/"',
            'href="https://github.com/pydantic/pydantic-ai/docs"',
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("Framework research note" in error for error in errors))

    def test_mcp_renamed_repository_is_accepted(self) -> None:
        text = filled_template().replace(
            'data-source-ids="pydantic-ai,google-adk"',
            'data-source-ids="pydantic-ai,mcp-spec"',
        ).replace(
            'href="https://google.github.io/adk-docs/"',
            'href="https://github.com/modelcontextprotocol/modelcontextprotocol"',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(text, encoding="utf-8")
            self.assertEqual(VALIDATOR.validate(path), [])

    def test_valid_paper_item_is_accepted(self) -> None:
        paper_html = (
            '<article class="axis-item paper-item" data-paper-pool="weekly-hot" '
            'data-heat-score="82" data-relevance-score="91">'
            '<div class="paper-selection-meta"><span class="paper-pool">本周高热</span>'
            '<span>Heat 82 · Research fit 91</span></div><h4>Paper</h4><p>Finding</p>'
            '<a href="https://arxiv.org/abs/1234">Original paper</a></article>'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(filled_template(evaluation_html=paper_html), encoding="utf-8")
            self.assertEqual(VALIDATOR.validate(path), [])

    def test_paper_item_requires_valid_pool_and_scores(self) -> None:
        paper_html = (
            '<article class="axis-item paper-item" data-paper-pool="popular" '
            'data-heat-score="unknown" data-relevance-score="101">'
            '<div class="paper-selection-meta">Bad metadata</div><h4>Paper</h4>'
            '<a href="https://arxiv.org/abs/1234">Original paper</a></article>'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(filled_template(evaluation_html=paper_html), encoding="utf-8")
            errors = VALIDATOR.validate(path)
        self.assertTrue(any("invalid paper item" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

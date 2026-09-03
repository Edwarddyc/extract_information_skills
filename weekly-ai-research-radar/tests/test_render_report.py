from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RENDERER = load("render_report", "render_report.py")
VALIDATOR = load("validate_html_report_for_renderer", "validate_html_report.py")


class RenderReportTests(unittest.TestCase):
    def test_structured_report_renders_and_validates(self) -> None:
        organizations = {
            "anthropic": ["claude-blog", "anthropic-research"],
            "openai": ["openai-engineering", "openai-research", "openai-news"],
            "hermes": ["hermes-repo"], "pi": ["pi-agent"],
            "deepseek-harness": ["deepseek-harness"], "agno": ["agno-repo"],
            "langchain": ["langchain-repo", "langgraph-repo", "langchain-blog"],
            "langfuse": ["langfuse-repo", "langfuse-blog"],
        }
        watch = []
        for organization, source_ids in organizations.items():
            for source_id in source_ids:
                watch.append({"source_id": source_id, "name": source_id, "organization": organization,
                              "state": "no-material-update", "checked_at": "2026-09-02"})
        data = {
            "meta": {"title": "Radar", "date_range": "2026-08-27 — 2026-09-02",
                     "report_end": "2026-09-02", "issue_number": "1", "generated_at": "now",
                     "deck": "Deck", "candidate_count": 10, "retained_count": 1,
                     "executive_judgment": "Judgment"},
            "priority_watch": watch,
            "top_signals": [{"axis": "Evaluation", "score": 90, "confidence": "high",
                             "title": "Signal", "change": "Change", "impact": "Impact",
                             "evidence": "Evidence", "action": "Action", "url": "https://arxiv.org/abs/2609.01234"}],
            "axes": {"framework": {"status": "No material signal", "studies": []},
                     "evaluation": {"status": "Active", "items": []},
                     "evolution": {"status": "Quiet", "items": []},
                     "product": {"status": "Quiet", "items": []}},
            "random_signal": {"seed": "2026-09-02", "title": "Random", "tension": "Tension",
                              "evidence": "Evidence", "source_url": "https://example.org/item",
                              "discussion_url": "https://news.ycombinator.com/item?id=1"},
            "research_queue": [], "coverage_gaps": [], "registry_changes": []
        }
        result = RENDERER.render(data, (ROOT / "assets" / "weekly-report-template.html").read_text(encoding="utf-8"))
        self.assertNotIn("{{", result)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(result, encoding="utf-8")
            self.assertEqual(VALIDATOR.validate(path), [])

    def test_source_text_is_escaped(self) -> None:
        self.assertEqual(RENDERER.e('<script>"x"</script>'), '&lt;script&gt;&quot;x&quot;&lt;/script&gt;')

    def test_raw_html_override_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "html_fragments is not supported"):
            RENDERER.replacements({"html_fragments": {"TOP_SIGNALS_HTML": "<article>Manual</article>"}})


if __name__ == "__main__":
    unittest.main()

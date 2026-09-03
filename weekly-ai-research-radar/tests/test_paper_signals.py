from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect_paper_signals.py"
SPEC = importlib.util.spec_from_file_location("collect_paper_signals", SCRIPT)
assert SPEC and SPEC.loader
PAPERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PAPERS)


class PaperSignalTests(unittest.TestCase):
    def test_arxiv_and_attention_signals_merge(self) -> None:
        atom = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
        <id>http://arxiv.org/abs/2609.01234v1</id><title>Agent Paper</title>
        <published>2026-09-02T12:00:00Z</published><summary>Evidence</summary>
        <link rel="alternate" href="https://arxiv.org/abs/2609.01234" />
        <author><name>A. Researcher</name></author></entry></feed>'''
        papers = PAPERS.parse_arxiv_atom(atom)
        hf = PAPERS.parse_attention_page(
            '<a href="/papers/2609.01234">Agent Paper 42 upvotes</a>', "huggingface"
        )
        github = PAPERS.parse_attention_page(
            '<a href="https://arxiv.org/abs/2609.01234">paper</a>', "github"
        )
        PAPERS.merge_signals(papers, [hf, github])
        heat = papers[0]["heat_signals"]
        self.assertEqual(heat["hf_weekly_rank"], 1)
        self.assertEqual(heat["hf_upvotes_7d"], 42)
        self.assertTrue(heat["github_weekly_trending"])
        self.assertEqual(heat["independent_sources_7d"], 2)


if __name__ == "__main__":
    unittest.main()

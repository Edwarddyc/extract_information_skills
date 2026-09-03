from __future__ import annotations

import importlib.util
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "select_paper_portfolio.py"
SPEC = importlib.util.spec_from_file_location("select_paper_portfolio", SCRIPT)
assert SPEC and SPEC.loader
PORTFOLIO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PORTFOLIO)


def paper(index: int, published: str, relevance: int, hot: bool = False) -> dict:
    signals = {
        "independent_sources_7d": 3 if hot else 0,
        "hf_weekly_rank": index if hot else 0,
        "hf_upvotes_7d": 80 if hot else 0,
        "github_weekly_trending": hot,
        "attention_events_7d": 20 if hot else 0,
        "attention_events_previous_7d": 4 if hot else 0,
    }
    return {
        "canonical_id": f"paper-{index}",
        "title": f"Paper {index}",
        "url": f"https://arxiv.org/abs/{index}",
        "published_at": published,
        "relevance_score": relevance,
        "heat_signals": signals,
    }


class PaperPortfolioTests(unittest.TestCase):
    def test_default_portfolio_is_seventy_thirty(self) -> None:
        candidates = [paper(i, "2026-08-15", 70 + i, hot=True) for i in range(1, 9)]
        candidates.extend(paper(i, "2026-08-30", 100 - i) for i in range(9, 14))
        selected, summary = PORTFOLIO.select_portfolio(
            candidates, report_end=date(2026, 9, 2)
        )
        self.assertEqual(summary["selected"]["weekly_hot"], 7)
        self.assertEqual(summary["selected"]["fresh_exploration"], 3)
        self.assertEqual(summary["selected"]["quota_backfill"], 0)
        self.assertEqual(len(selected), 10)

    def test_delayed_breakout_can_enter_hot_pool(self) -> None:
        candidates = [paper(1, "2026-08-05", 95, hot=True)]
        selected, _ = PORTFOLIO.select_portfolio(
            candidates, report_end=date(2026, 9, 2), limit=1
        )
        self.assertEqual(selected[0]["paper_pool"], "weekly-hot")

    def test_single_platform_signal_is_not_high_heat(self) -> None:
        candidate = paper(1, "2026-08-30", 95)
        candidate["heat_signals"] = {"hf_weekly_rank": 1, "hf_upvotes_7d": 100}
        selected, summary = PORTFOLIO.select_portfolio(
            [candidate], report_end=date(2026, 9, 2), limit=1
        )
        self.assertEqual(summary["selected"]["weekly_hot"], 0)
        self.assertEqual(selected[0]["paper_pool"], "fresh-exploration")

    def test_outside_candidate_window_is_removed(self) -> None:
        selected, summary = PORTFOLIO.select_portfolio(
            [paper(1, "2026-07-01", 99, hot=True)],
            report_end=date(2026, 9, 2),
        )
        self.assertEqual(selected, [])
        self.assertEqual(summary["eligible_candidates"], 0)

    def test_arxiv_pdf_and_abstract_are_deduplicated(self) -> None:
        first = paper(1, "2026-08-30", 80)
        first.pop("canonical_id")
        second = dict(first, url="https://arxiv.org/pdf/1.pdf", relevance_score=90)
        selected, summary = PORTFOLIO.select_portfolio(
            [first, second], report_end=date(2026, 9, 2), limit=2
        )
        self.assertEqual(summary["eligible_candidates"], 1)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["relevance_score"], 90)


if __name__ == "__main__":
    unittest.main()

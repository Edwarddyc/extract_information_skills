from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "select_random_signal.py"
SPEC = importlib.util.spec_from_file_location("select_random_signal", SCRIPT)
assert SPEC and SPEC.loader
SIGNALS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SIGNALS)


class RandomSignalTests(unittest.TestCase):
    def test_selection_is_stable_for_week_seed(self) -> None:
        candidates = [
            {"title": "A", "url": "https://example.com/a"},
            {"title": "B", "url": "https://example.com/b"},
        ]
        first = SIGNALS.select(candidates, "2026-08-28")
        second = SIGNALS.select(list(reversed(candidates)), "2026-08-28")
        self.assertEqual(first, second)

    def test_loader_filters_to_hacker_news(self) -> None:
        rows = [
            {"source_id": "hacker-news", "title": "A", "url": "https://example.com/a"},
            {"source_id": "other", "title": "B", "url": "https://example.com/b"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            loaded = SIGNALS.load_candidates(path, "hacker-news")
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], "A")


if __name__ == "__main__":
    unittest.main()

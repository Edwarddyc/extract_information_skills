from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_watchlist.py"
SPEC = importlib.util.spec_from_file_location("validate_watchlist", SCRIPT)
assert SPEC and SPEC.loader
WATCHLIST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WATCHLIST)


class WatchlistTests(unittest.TestCase):
    def test_project_watchlist_is_valid(self) -> None:
        errors = WATCHLIST.validate(
            ROOT / "data" / "priority-watchlist.csv",
            ROOT / "data" / "source-registry.csv",
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_page_sources.py"
SPEC = importlib.util.spec_from_file_location("fetch_page_sources", SCRIPT)
assert SPEC and SPEC.loader
PAGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PAGES)


class PageParserTests(unittest.TestCase):
    def test_json_ld_and_article_cards_are_extracted(self) -> None:
        html = """
        <script type="application/ld+json">{"@type":"BlogPosting","headline":"JSON story",
        "url":"/blog/json-story","datePublished":"2026-09-01"}</script>
        <article><a href="/research/card-story">Card story title</a>
        <time datetime="2026-09-02">September 2</time></article>
        """
        items = PAGES.parse_page(html, "https://example.com/blog")
        self.assertEqual({item["title"] for item in items}, {"JSON story", "Card story title"})
        self.assertTrue(all(item["url"].startswith("https://example.com/") for item in items))

    def test_duplicate_url_prefers_dated_record(self) -> None:
        html = '<a href="/blog/story">A useful story title</a><article><a href="/blog/story">A useful story title</a><time datetime="2026-09-01"></time></article>'
        items = PAGES.parse_page(html, "https://example.com/blog")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["published_raw"], "2026-09-01")

if __name__ == "__main__":
    unittest.main()

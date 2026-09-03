from __future__ import annotations

import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_public_feeds.py"
SPEC = importlib.util.spec_from_file_location("fetch_public_feeds", SCRIPT)
assert SPEC and SPEC.loader
FEEDS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FEEDS)


class FeedParserTests(unittest.TestCase):
    def test_rss(self) -> None:
        root = ET.fromstring(
            """<rss><channel><item><title>Agent release</title>
            <link>https://example.com/release</link>
            <comments>https://news.ycombinator.com/item?id=1</comments>
            <pubDate>Thu, 27 Aug 2026 10:00:00 GMT</pubDate>
            <description>Architecture update</description></item></channel></rss>"""
        )
        items = list(FEEDS.rss_items(root))
        self.assertEqual(items[0]["title"], "Agent release")
        self.assertEqual(items[0]["url"], "https://example.com/release")
        self.assertEqual(items[0]["discussion_url"], "https://news.ycombinator.com/item?id=1")
        self.assertIsNotNone(FEEDS.parse_date(items[0]["published_raw"]))

    def test_atom(self) -> None:
        root = ET.fromstring(
            """<feed xmlns="http://www.w3.org/2005/Atom"><entry>
            <title>Benchmark update</title>
            <link href="https://example.com/benchmark" />
            <updated>2026-08-27T10:00:00Z</updated>
            <summary>New cost results</summary></entry></feed>"""
        )
        items = list(FEEDS.atom_items(root))
        self.assertEqual(items[0]["title"], "Benchmark update")
        self.assertEqual(items[0]["url"], "https://example.com/benchmark")
        self.assertIsNotNone(FEEDS.parse_date(items[0]["published_raw"]))


if __name__ == "__main__":
    unittest.main()

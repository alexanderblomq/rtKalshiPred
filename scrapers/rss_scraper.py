from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

from scrapers.article_scraper import ArticleScraper
from utils.review_discovery_shared import prioritize_candidate_urls


class RSSScraper(ArticleScraper):
    source_name = "rss"

    def list_recent_urls(self) -> List[str]:
        if not self.rule.discovery_url:
            return []

        xml_text = self.fetch_text(self.rule.discovery_url)
        root = ET.fromstring(xml_text)

        urls = []
        for item in root.findall(".//item/link"):
            if item.text and self._is_allowed_review_url(item.text.strip()):
                urls.append(item.text.strip())

        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}link"):
            href = entry.attrib.get("href")
            if href and self._is_allowed_review_url(href.strip()):
                urls.append(href.strip())

        return prioritize_candidate_urls(
            urls,
            rule=self.rule,
            publication=self.publication,
            limit=24,
        )

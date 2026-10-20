from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

from scrapers.article_scraper import ArticleScraper
from utils.review_discovery_shared import prioritize_candidate_urls


class SitemapScraper(ArticleScraper):
    source_name = "sitemap"

    def list_recent_urls(self) -> List[str]:
        if not self.rule.discovery_url:
            return []

        xml_text = self.fetch_text(self.rule.discovery_url)
        root = ET.fromstring(xml_text)

        urls = []
        for loc in root.findall(".//{*}loc"):
            if loc.text and self._is_allowed_review_url(loc.text.strip()):
                urls.append(loc.text.strip())
        return prioritize_candidate_urls(
            urls,
            rule=self.rule,
            publication=self.publication,
            limit=32,
        )

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from scrapers.article_scraper import ArticleScraper
from scrapers.base_scraper import BaseScraper, PublicationConfig, SourceRule
from scrapers.rss_scraper import RSSScraper
from scrapers.sitemap_scraper import SitemapScraper


SCRAPER_TYPES = {
    "article": ArticleScraper,
    "rss": RSSScraper,
    "sitemap": SitemapScraper,
}


@dataclass
class RegistryView:
    publications: Tuple[PublicationConfig, ...]
    rules: Dict[str, SourceRule]
    _scraper_cache: Dict[bool, Tuple[BaseScraper, ...]] = field(default_factory=dict, init=False, repr=False)

    def get_scrapers(self, include_disabled: bool = False) -> Tuple[BaseScraper, ...]:
        if include_disabled not in self._scraper_cache:
            self._scraper_cache[include_disabled] = tuple(
                build_scrapers(self.publications, self.rules, include_disabled=include_disabled)
            )
        return self._scraper_cache[include_disabled]


def load_registries(publication_registry_path: str, source_rules_path: str) -> Tuple[List[PublicationConfig], Dict[str, SourceRule]]:
    publications_payload = json.loads(Path(publication_registry_path).read_text(encoding="utf-8"))
    rules_payload = json.loads(Path(source_rules_path).read_text(encoding="utf-8"))

    publications = [PublicationConfig.from_dict(item) for item in publications_payload]
    rules = {item["publication_id"]: SourceRule(**item) for item in rules_payload}
    return publications, rules


def load_runtime_view(publication_registry_path: str, source_rules_path: str) -> RegistryView:
    publication_path = Path(publication_registry_path).resolve()
    rules_path = Path(source_rules_path).resolve()
    return _load_runtime_view_cached(
        str(publication_path),
        publication_path.stat().st_mtime_ns,
        str(rules_path),
        rules_path.stat().st_mtime_ns,
    )


@lru_cache(maxsize=8)
def _load_runtime_view_cached(
    publication_registry_path: str,
    publication_registry_mtime_ns: int,
    source_rules_path: str,
    source_rules_mtime_ns: int,
) -> RegistryView:
    del publication_registry_mtime_ns
    del source_rules_mtime_ns
    publications, rules = load_registries(publication_registry_path, source_rules_path)
    return RegistryView(publications=tuple(publications), rules=rules)


def build_scrapers(
    publications: Iterable[PublicationConfig],
    rules: Dict[str, SourceRule],
    include_disabled: bool = False,
) -> List[BaseScraper]:
    scrapers: List[BaseScraper] = []
    for publication in publications:
        if not include_disabled and not publication.enabled:
            continue

        rule = rules.get(publication.publication_id)
        if not rule:
            continue

        adapter = rule.adapter or publication.adapter or publication.source_type
        scraper_cls = SCRAPER_TYPES.get(adapter)
        if scraper_cls is None:
            continue

        scrapers.append(scraper_cls(publication, rule))
    return scrapers

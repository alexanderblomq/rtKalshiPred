from __future__ import annotations

import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

from scrapers.factory import RegistryView, build_scrapers, load_registries
from utils.review_discovery_shared import (
    is_allowed_review_url,
    prioritize_candidate_urls,
    process_url_candidate,
    publication_priority_key,
    review_candidate_sort_key,
)


DEFAULT_PUBLICATION_REGISTRY = "data/critics/publication_registry.json"
DEFAULT_SOURCE_RULES = "data/critics/source_rules.json"

HOST_SEARCH_TEMPLATES = {
    "variety.com": [
        "https://variety.com/?s={query}",
    ],
    "www.rogerebert.com": [
        "https://www.rogerebert.com/search?search={query}",
    ],
    "www.newyorker.com": [
        "https://www.newyorker.com/search?q={query}",
    ],
    "411mania.com": [
        "https://411mania.com/?s={query}",
    ],
    "4columns.org": [
        "https://4columns.org/?s={query}",
    ],
}

GENERIC_SEARCH_TEMPLATES = [
    "{base}/?s={query}",
    "{base}/search?q={query}",
    "{base}/search?query={query}",
    "{base}/search/{query_slug}",
]


class TitleSearchBackfiller:
    def __init__(
        self,
        publication_registry_path: str = DEFAULT_PUBLICATION_REGISTRY,
        source_rules_path: str = DEFAULT_SOURCE_RULES,
        include_disabled: bool = True,
        runtime_view: Optional[RegistryView] = None,
    ) -> None:
        self.publication_registry_path = publication_registry_path
        self.source_rules_path = source_rules_path
        self.include_disabled = include_disabled
        self.runtime_view = runtime_view

    def build_scrapers(self):
        if self.runtime_view is not None:
            scrapers = list(self.runtime_view.get_scrapers(include_disabled=self.include_disabled))
        else:
            publications, rules = load_registries(self.publication_registry_path, self.source_rules_path)
            scrapers = build_scrapers(publications, rules, include_disabled=self.include_disabled)
        scrapers.sort(key=lambda scraper: publication_priority_key(scraper.publication, scraper.rule))
        return scrapers

    def search(
        self,
        title: str,
        max_publications: Optional[int] = None,
        max_search_urls_per_publication: int = 2,
        max_candidate_urls_per_publication: int = 8,
        publication_workers: int = 16,
        scrape_workers: int = 24,
        min_confidence: float = 0.6,
        min_review_likeness: float = 0.45,
        publication_ids: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        scrapers = self.build_scrapers()
        if publication_ids:
            wanted = set(publication_ids)
            scrapers = [scraper for scraper in scrapers if scraper.publication.publication_id in wanted]
        if max_publications is not None:
            scrapers = scrapers[:max_publications]

        results: List[Dict[str, Any]] = []
        publication_attempts = len(scrapers)
        publications_with_search_pages = 0
        publications_with_candidates = 0
        candidate_url_count = 0
        completed_publications = 0

        with ThreadPoolExecutor(max_workers=min(publication_workers, max(1, len(scrapers)))) as executor:
            future_map = {
                executor.submit(
                    self._search_publication,
                    scraper,
                    title,
                    max_search_urls_per_publication,
                    max_candidate_urls_per_publication,
                    scrape_workers,
                    min_confidence,
                    min_review_likeness,
                ): scraper
                for scraper in scrapers
            }
            for future in as_completed(future_map):
                payload = future.result()
                completed_publications += 1
                if payload["search_page_count"] > 0:
                    publications_with_search_pages += 1
                if payload["candidate_url_count"] > 0:
                    publications_with_candidates += 1
                candidate_url_count += payload["candidate_url_count"]
                results.extend(payload["results"])
                if progress_callback:
                    progress_callback(
                        {
                            "phase": "backfill_title_search",
                            "completed": completed_publications,
                            "total": publication_attempts,
                            "candidate_url_count": candidate_url_count,
                            "publications_with_search_pages": publications_with_search_pages,
                            "publications_with_candidates": publications_with_candidates,
                        }
                    )

        results.sort(key=review_candidate_sort_key)
        deduped = []
        seen_urls = set()
        for result in results:
            url = result["url"]
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deduped.append(result)

        return {
            "results": deduped,
            "publication_attempts": publication_attempts,
            "publications_with_search_pages": publications_with_search_pages,
            "publications_with_candidates": publications_with_candidates,
            "candidate_url_count": candidate_url_count,
        }

    def _search_publication(
        self,
        scraper,
        title: str,
        max_search_urls_per_publication: int,
        max_candidate_urls_per_publication: int,
        scrape_workers: int,
        min_confidence: float,
        min_review_likeness: float,
    ) -> Dict[str, Any]:
        search_urls = self._build_search_urls(scraper, title)[:max_search_urls_per_publication]
        search_page_count = 0
        candidate_urls: List[str] = []
        for search_url in search_urls:
            try:
                html_text = scraper.fetch_text(search_url)
            except Exception:
                continue
            search_page_count += 1
            candidate_urls.extend(self._extract_candidate_urls(scraper, search_url, html_text))

        deduped_candidates = prioritize_candidate_urls(
            candidate_urls,
            rule=getattr(scraper, "rule", None),
            publication=getattr(scraper, "publication", None),
            title=title,
            limit=max_candidate_urls_per_publication,
            require_title_match=True,
        )
        if not deduped_candidates:
            return {
                "results": [],
                "search_page_count": search_page_count,
                "candidate_url_count": 0,
            }

        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(scrape_workers, max(1, len(deduped_candidates)))) as executor:
            future_map = {
                executor.submit(self._score_candidate, scraper, title, url, min_review_likeness): url
                for url in deduped_candidates
            }
            for future in as_completed(future_map):
                result = future.result()
                if result and result["match_confidence"] >= min_confidence:
                    results.append(result)

        results.sort(key=review_candidate_sort_key)
        return {
            "results": results,
            "search_page_count": search_page_count,
            "candidate_url_count": len(deduped_candidates),
        }

    def _build_search_urls(self, scraper, title: str) -> List[str]:
        base_url = scraper.publication.site_base_url or scraper.rule.discovery_url
        if not base_url:
            return []

        parsed = urlparse(base_url)
        host = parsed.netloc.lower()
        query = quote_plus(title)
        query_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

        templates = list(HOST_SEARCH_TEMPLATES.get(host, []))
        templates.extend(GENERIC_SEARCH_TEMPLATES)

        urls = []
        for template in templates:
            if "{base}" in template:
                candidate = template.format(base=base_url.rstrip("/"), query=query, query_slug=query_slug)
            else:
                candidate = template.format(query=query, query_slug=query_slug)
            urls.append(candidate)
        return list(dict.fromkeys(urls))

    def _extract_candidate_urls(self, scraper, search_url: str, html_text: str) -> List[str]:
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_text, flags=re.IGNORECASE)
        urls = []
        for href in hrefs:
            absolute = urljoin(search_url, href)
            if is_allowed_review_url(scraper.rule, absolute):
                urls.append(absolute)
        return urls

    def _score_candidate(self, scraper, title: str, url: str, min_review_likeness: float) -> Optional[Dict[str, Any]]:
        return process_url_candidate(
            scraper=scraper,
            title=title,
            url=url,
            min_review_likeness=min_review_likeness,
            extra_fields={"search_mode": "title_search"},
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Title-targeted publication search backfill.")
    parser.add_argument("title", type=str)
    parser.add_argument("--max-publications", type=int, default=None)
    parser.add_argument("--publication-workers", type=int, default=16)
    parser.add_argument("--scrape-workers", type=int, default=24)
    parser.add_argument("--min-confidence", type=float, default=0.6)
    parser.add_argument("--min-review-likeness", type=float, default=0.45)
    parser.add_argument("--publication-id", action="append", dest="publication_ids")
    args = parser.parse_args()

    backfiller = TitleSearchBackfiller()
    result = backfiller.search(
        title=args.title,
        max_publications=args.max_publications,
        publication_workers=args.publication_workers,
        scrape_workers=args.scrape_workers,
        min_confidence=args.min_confidence,
        min_review_likeness=args.min_review_likeness,
        publication_ids=args.publication_ids,
    )
    for item in result["results"][:100]:
        print(item)
    print({k: v for k, v in result.items() if k != "results"})


if __name__ == "__main__":
    main()

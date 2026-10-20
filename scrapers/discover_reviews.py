from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from pipelines.enrich_publications import sort_publications_by_value
from scrapers.factory import RegistryView, build_scrapers, load_registries
from utils.review_discovery_shared import prioritize_candidate_urls, process_url_candidate, review_candidate_sort_key


DEFAULT_PUBLICATION_REGISTRY = "data/critics/publication_registry.json"
DEFAULT_SOURCE_RULES = "data/critics/source_rules.json"


class ReviewDiscoverer:
    def __init__(
        self,
        publication_registry_path: str = DEFAULT_PUBLICATION_REGISTRY,
        source_rules_path: str = DEFAULT_SOURCE_RULES,
        include_disabled: bool = True,
        runtime_view: Optional[RegistryView] = None,
    ):
        self.publication_registry_path = publication_registry_path
        self.source_rules_path = source_rules_path
        self.include_disabled = include_disabled
        self.runtime_view = runtime_view

    def build_scrapers(self):
        if self.runtime_view is not None:
            publications = list(self.runtime_view.publications)
            rules = self.runtime_view.rules
        else:
            publications, rules = load_registries(self.publication_registry_path, self.source_rules_path)
        publications = [publication for publication in publications if publication.site_base_url or publication.enabled]
        ordered_publication_dicts = sort_publications_by_value(
            [
                {
                    "publication_id": publication.publication_id,
                    "outlet_name": publication.outlet_name,
                    "approved_publication": publication.approved_publication,
                    "critic_names": publication.critic_names,
                    "site_base_url": publication.site_base_url,
                    "enabled": publication.enabled,
                }
                for publication in publications
            ]
        )
        publications_by_id = {publication.publication_id: publication for publication in publications}
        ordered_publications = [
            publications_by_id[item["publication_id"]]
            for item in ordered_publication_dicts
            if item["publication_id"] in publications_by_id
        ]
        return build_scrapers(ordered_publications, rules, include_disabled=self.include_disabled)

    def discover(
        self,
        title: str,
        max_publications: Optional[int] = None,
        max_urls_per_publication: int = 12,
        publication_workers: int = 16,
        scrape_workers: int = 24,
        min_confidence: float = 0.6,
        min_review_likeness: float = 0.45,
        publication_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        return self.discover_with_metadata(
            title=title,
            max_publications=max_publications,
            max_urls_per_publication=max_urls_per_publication,
            publication_workers=publication_workers,
            scrape_workers=scrape_workers,
            min_confidence=min_confidence,
            min_review_likeness=min_review_likeness,
            publication_ids=publication_ids,
        )["results"]

    def discover_with_metadata(
        self,
        title: str,
        max_publications: Optional[int] = None,
        max_urls_per_publication: int = 12,
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

        publication_results: List[Dict[str, Any]] = []
        publication_attempts = len(scrapers)
        publications_with_urls = 0
        publications_with_matches = 0
        candidate_url_count = 0
        completed_publications = 0
        with ThreadPoolExecutor(max_workers=publication_workers) as executor:
            future_map = {
                executor.submit(
                    self._discover_from_publication,
                    scraper,
                    title,
                    max_urls_per_publication,
                    scrape_workers,
                    min_confidence,
                    min_review_likeness,
                ): scraper
                for scraper in scrapers
            }
            for future in as_completed(future_map):
                result = future.result()
                completed_publications += 1
                candidate_url_count += int(result["candidate_url_count"])
                if result["candidate_url_count"] > 0:
                    publications_with_urls += 1
                if result["results"]:
                    publications_with_matches += 1
                    publication_results.extend(result["results"])
                if progress_callback:
                    progress_callback(
                        {
                            "phase": "backfill_recent_discovery",
                            "completed": completed_publications,
                            "total": publication_attempts,
                            "candidate_url_count": candidate_url_count,
                            "publications_with_urls": publications_with_urls,
                            "publications_with_matches": publications_with_matches,
                        }
                    )

        publication_results.sort(key=review_candidate_sort_key)
        return {
            "results": publication_results,
            "publication_attempts": publication_attempts,
            "publications_with_urls": publications_with_urls,
            "publications_with_matches": publications_with_matches,
            "candidate_url_count": candidate_url_count,
        }

    def _discover_from_publication(
        self,
        scraper,
        title: str,
        max_urls_per_publication: int,
        scrape_workers: int,
        min_confidence: float,
        min_review_likeness: float,
    ) -> Dict[str, Any]:
        try:
            urls = prioritize_candidate_urls(
                scraper.list_recent_urls(),
                rule=getattr(scraper, "rule", None),
                publication=getattr(scraper, "publication", None),
                title=title,
                limit=max_urls_per_publication,
                require_title_match=True,
            )
        except Exception:
            return {"results": [], "candidate_url_count": 0}

        if not urls:
            return {"results": [], "candidate_url_count": 0}

        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(scrape_workers, max(1, len(urls)))) as executor:
            future_map = {
                executor.submit(self._score_url_candidate, scraper, title, url, min_review_likeness): url
                for url in urls
            }
            for future in as_completed(future_map):
                candidate = future.result()
                if candidate and candidate["match_confidence"] >= min_confidence:
                    results.append(candidate)

        results.sort(key=review_candidate_sort_key)
        return {"results": results, "candidate_url_count": len(urls)}

    def _score_url_candidate(self, scraper, title: str, url: str, min_review_likeness: float) -> Optional[Dict[str, Any]]:
        return process_url_candidate(
            scraper=scraper,
            title=title,
            url=url,
            min_review_likeness=min_review_likeness,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover likely critic reviews for a movie across the publication registry.")
    parser.add_argument("title", type=str, help="Movie title to search for")
    parser.add_argument("--max-publications", type=int, default=None)
    parser.add_argument("--max-urls-per-publication", type=int, default=20)
    parser.add_argument("--publication-workers", type=int, default=16)
    parser.add_argument("--scrape-workers", type=int, default=24)
    parser.add_argument("--min-confidence", type=float, default=0.6)
    parser.add_argument("--min-review-likeness", type=float, default=0.45)
    parser.add_argument("--publication-id", action="append", dest="publication_ids")
    args = parser.parse_args()

    discoverer = ReviewDiscoverer()
    results = discoverer.discover(
        title=args.title,
        max_publications=args.max_publications,
        max_urls_per_publication=args.max_urls_per_publication,
        publication_workers=args.publication_workers,
        scrape_workers=args.scrape_workers,
        min_confidence=args.min_confidence,
        min_review_likeness=args.min_review_likeness,
        publication_ids=args.publication_ids,
    )

    for result in results[:100]:
        print(result)


if __name__ == "__main__":
    main()

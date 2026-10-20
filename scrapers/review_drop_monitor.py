from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from typing import Callable, Dict, Iterable, List, Any, Optional, Set

from scrapers.factory import RegistryView, build_scrapers, load_registries
from utils.review_discovery_shared import prioritize_candidate_urls, publication_priority_key


DEFAULT_PUBLICATION_REGISTRY = "data/critics/publication_registry.json"
DEFAULT_SOURCE_RULES = "data/critics/source_rules.json"
DEFAULT_POLL_WORKERS = 24
DEFAULT_MAX_URLS_PER_PUBLICATION = 8


class ReviewDropMonitor:
    def __init__(
        self,
        publication_registry_path: str = DEFAULT_PUBLICATION_REGISTRY,
        source_rules_path: str = DEFAULT_SOURCE_RULES,
        include_disabled: bool = False,
        publication_ids: Optional[List[str]] = None,
        poll_workers: int = DEFAULT_POLL_WORKERS,
        max_urls_per_publication: int = DEFAULT_MAX_URLS_PER_PUBLICATION,
        logger: Optional[logging.Logger] = None,
        runtime_view: Optional[RegistryView] = None,
    ):
        self.publication_registry_path = publication_registry_path
        self.source_rules_path = source_rules_path
        self.include_disabled = include_disabled
        self.publication_ids = set(publication_ids or [])
        self.poll_workers = poll_workers
        self.max_urls_per_publication = max_urls_per_publication
        self.seen_urls: Set[str] = set()
        self.logger = logger
        self.runtime_view = runtime_view
        self._failure_streaks: Dict[str, int] = {}
        self._backoff_until_poll: Dict[str, int] = {}
        self._poll_counter = 0

    def build_scrapers(self):
        if self.runtime_view is not None:
            scrapers = list(self.runtime_view.get_scrapers(include_disabled=self.include_disabled))
        else:
            publications, rules = load_registries(self.publication_registry_path, self.source_rules_path)
            scrapers = build_scrapers(publications, rules, include_disabled=self.include_disabled)
        if self.publication_ids:
            scrapers = [scraper for scraper in scrapers if scraper.publication.publication_id in self.publication_ids]
        scrapers.sort(key=lambda scraper: publication_priority_key(scraper.publication, scraper.rule))
        return scrapers

    def poll_review_sources(self) -> List[Dict[str, Any]]:
        return self.poll_review_sources_with_metadata()["events"]

    def poll_review_sources_with_metadata(
        self,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_events: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._poll_counter += 1
        scrapers = self.build_scrapers()
        eligible_scrapers = [
            scraper
            for scraper in scrapers
            if self._backoff_until_poll.get(scraper.publication.publication_id, 0) <= self._poll_counter
        ]
        pending_events: List[Dict[str, Any]] = []
        scraper_failures = 0
        completed_scrapers = 0
        skipped_scrapers = len(scrapers) - len(eligible_scrapers)
        if self.logger:
            self.logger.info(
                "poll_start scraper_count=%s eligible_scraper_count=%s skipped_scrapers=%s poll_workers=%s max_urls_per_publication=%s",
                len(scrapers),
                len(eligible_scrapers),
                skipped_scrapers,
                self.poll_workers,
                self.max_urls_per_publication,
            )

        with ThreadPoolExecutor(max_workers=min(self.poll_workers, max(1, len(eligible_scrapers)))) as executor:
            future_map = {
                executor.submit(self._list_urls_for_scraper, scraper): scraper
                for scraper in eligible_scrapers
            }
            for future in as_completed(future_map):
                payload = future.result()
                completed_scrapers += 1
                if payload is None:
                    scraper_failures += 1
                    if progress_callback:
                        progress_callback(
                            {
                                "phase": "poll_discovery",
                                "completed": completed_scrapers,
                                "total": len(eligible_scrapers),
                                "scraper_failures": scraper_failures,
                                "discovered_url_count": len(pending_events),
                                "skipped_scrapers": skipped_scrapers,
                            }
                        )
                    continue
                if self.logger:
                    self.logger.debug(
                        "poll_scraper_success publication_id=%s url_count=%s source_type=%s",
                        payload["publication_id"],
                        len(payload["urls"]),
                        payload["source_type"],
                    )
                for url in payload["urls"]:
                    if url in self.seen_urls:
                        continue
                    pending_events.append(
                        {
                            "event_type": "review_url_discovered",
                            "publication_id": payload["publication_id"],
                            "outlet_name": payload["outlet_name"],
                            "url": url,
                            "source_type": payload["source_type"],
                        }
                    )
                if progress_callback:
                    progress_callback(
                        {
                            "phase": "poll_discovery",
                            "completed": completed_scrapers,
                            "total": len(eligible_scrapers),
                            "scraper_failures": scraper_failures,
                            "discovered_url_count": len(pending_events),
                            "skipped_scrapers": skipped_scrapers,
                        }
                    )

        pending_events.sort(key=lambda item: (item["publication_id"], item["url"]))
        total_candidate_event_count = len(pending_events)
        events = pending_events[:max_events] if max_events is not None else pending_events
        for event in events:
            self.seen_urls.add(event["url"])
        if self.logger:
            self.logger.info(
                "poll_complete discovered_url_count=%s total_candidate_event_count=%s scraper_count=%s scraper_failures=%s",
                len(events),
                total_candidate_event_count,
                len(eligible_scrapers),
                scraper_failures,
            )
        return {
            "events": events,
            "scraper_count": len(eligible_scrapers),
            "scraper_failures": scraper_failures,
            "total_candidate_event_count": total_candidate_event_count,
            "skipped_scrapers": skipped_scrapers,
        }

    def _list_urls_for_scraper(self, scraper) -> Optional[Dict[str, Any]]:
        publication_id = scraper.publication.publication_id
        try:
            urls = prioritize_candidate_urls(
                scraper.list_recent_urls(),
                rule=getattr(scraper, "rule", None),
                publication=getattr(scraper, "publication", None),
                limit=self.max_urls_per_publication,
            )
        except Exception as exc:
            failure_streak = self._failure_streaks.get(publication_id, 0) + 1
            self._failure_streaks[publication_id] = failure_streak
            if failure_streak >= 2:
                self._backoff_until_poll[publication_id] = self._poll_counter + min(8, 2 ** (failure_streak - 1))
            if self.logger:
                self.logger.warning(
                    "poll_scraper_failed publication_id=%s outlet_name=%s error=%s",
                    publication_id,
                    scraper.publication.outlet_name,
                    exc,
                )
            return None
        self._failure_streaks[publication_id] = 0
        self._backoff_until_poll.pop(publication_id, None)
        return {
            "publication_id": publication_id,
            "outlet_name": scraper.publication.outlet_name,
            "source_type": scraper.source_name,
            "urls": list(urls),
        }


def poll_review_sources(
    publication_registry_path: str = DEFAULT_PUBLICATION_REGISTRY,
    source_rules_path: str = DEFAULT_SOURCE_RULES,
    include_disabled: bool = False,
    publication_ids: Optional[List[str]] = None,
    poll_workers: int = DEFAULT_POLL_WORKERS,
) -> List[Dict[str, Any]]:
    """Convenience wrapper for one-shot polling."""
    monitor = ReviewDropMonitor(
        publication_registry_path,
        source_rules_path,
        include_disabled=include_disabled,
        publication_ids=publication_ids,
        poll_workers=poll_workers,
    )
    return monitor.poll_review_sources()


def emit_new_events(events: Iterable[Dict[str, Any]], sink: Optional[list] = None) -> None:
    """Placeholder event sink."""
    if sink is None:
        for _event in events:
            pass
        return

    sink.extend(events)

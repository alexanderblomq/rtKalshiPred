from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from scrapers.discover_reviews import ReviewDiscoverer
from models.review_classifier import predict_review_freshness
from scrapers.rt_client import fetch_rt_title_baseline
from scrapers.review_candidate_filter import classify_review_candidate
from scrapers.review_drop_monitor import DEFAULT_POLL_WORKERS, ReviewDropMonitor
from scrapers.review_scraper import scrape_review
from scrapers.factory import RegistryView, load_runtime_view
from settings import RT_POLL_INTERVAL_SECONDS
from core.state_store import FileSystemRealtimeStateStore, RealtimeStateStore
from scrapers.title_search_backfill import TitleSearchBackfiller
from scrapers.title_matcher import match_title
from utils.logging import configure_file_logger
from core.state_store import slugify_title


ReviewDict = Dict[str, Any]


def format_clean_snapshot(snapshot: Dict[str, Any], phase: str = "poll") -> str:
    score = snapshot.get("calculated_tomatometer")
    score_text = "N/A" if score is None else f"{score:.2f}%"
    system_review_count = int(snapshot.get("system_review_count", snapshot.get("review_count", 0)))
    rt_review_count = snapshot.get("official_rt_review_count")
    rt_review_text = "N/A" if rt_review_count is None else str(int(rt_review_count))
    rt_tomatometer = snapshot.get("official_rt_tomatometer")
    rt_score_text = "N/A" if rt_tomatometer is None else f"{float(rt_tomatometer):.0f}%"
    rt_diagnostics = snapshot.get("official_rt_diagnostics") or {}
    accepted_key = "accepted_in_backfill" if phase == "backfill" else "accepted_this_poll"
    accepted_count = int(snapshot.get(accepted_key, 0))
    latest_reviews = snapshot.get("latest_reviews") or []
    latest = latest_reviews[-1] if latest_reviews else None

    lines = [
        f"{snapshot.get('target_title', 'Unknown Title')}",
        f"Predicted RT: {score_text} | System Reviews: {system_review_count} | Official RT Reviews: {rt_review_text} | New This Cycle: {accepted_count}",
        f"Official RT Score: {rt_score_text}",
    ]
    if rt_diagnostics.get("message"):
        lines.append(f"RT Sync: {rt_diagnostics['message']}")

    if latest:
        outlet = latest.get("outlet_name") or latest.get("publication_id") or "unknown outlet"
        headline = latest.get("headline") or latest.get("url") or "unknown review"
        fresh_probability = latest.get("fresh_probability")
        fresh_text = "N/A" if fresh_probability is None else f"{float(fresh_probability) * 100.0:.1f}% fresh"
        lines.append(f"Latest: {outlet} | {fresh_text} | {headline}")
    else:
        lines.append("Latest: none")

    return "\n".join(lines)


def format_status_message(title: str, message: str) -> str:
    return f"{title}\n{message}"


def format_completion_message(title: str, label: str, details: str) -> str:
    return f"{title}\n{label}: {details}"


def format_health_report(snapshot: Dict[str, Any], phase: str = "poll") -> str:
    if phase == "backfill":
        lines = [
            "Health Report",
            f"Recent publication attempts: {snapshot.get('backfill_recent_publication_attempts', 0)}",
            f"Recent publications with URLs: {snapshot.get('backfill_recent_publications_with_urls', 0)}",
            f"Recent candidate URLs: {snapshot.get('backfill_recent_candidate_url_count', 0)}",
            f"Title-search publication attempts: {snapshot.get('backfill_title_search_publication_attempts', 0)}",
            f"Title-search publications with pages: {snapshot.get('backfill_title_search_publications_with_search_pages', 0)}",
            f"Title-search candidate URLs: {snapshot.get('backfill_title_search_candidate_url_count', 0)}",
            f"Accepted in backfill: {snapshot.get('accepted_in_backfill', 0)}",
        ]
    else:
        lines = [
            "Health Report",
            f"Scrapers attempted: {snapshot.get('scraper_count', 0)}",
            f"Scrapers skipped (backoff): {snapshot.get('skipped_scrapers', 0)}",
            f"Scraper failures: {snapshot.get('scraper_failures', 0)}",
            f"Discovered URLs: {snapshot.get('discovered_url_count', 0)}",
            f"Accepted this poll: {snapshot.get('accepted_this_poll', 0)}",
            f"Rejected total: {snapshot.get('rejected_event_count', 0)}",
        ]
    diagnostics = snapshot.get("official_rt_diagnostics") or {}
    if diagnostics.get("message"):
        lines.append(f"RT diagnostics: {diagnostics['message']}")
    return "\n".join(lines)


@dataclass
class RealtimeTomatometerEngine:
    target_title: str
    publication_registry_path: str = "data/critics/publication_registry.json"
    source_rules_path: str = "data/critics/source_rules.json"
    include_disabled: bool = False
    publication_ids: Optional[List[str]] = None
    min_title_confidence: float = 0.6
    min_review_likeness: float = 0.45
    fresh_cutoff: float = 0.5
    poll_workers: int = DEFAULT_POLL_WORKERS
    process_workers: int = DEFAULT_POLL_WORKERS
    monitor: Optional[ReviewDropMonitor] = None
    discoverer: Optional[ReviewDiscoverer] = None
    title_search_backfiller: Optional[TitleSearchBackfiller] = None
    state_store: Optional[RealtimeStateStore] = None
    logger: Optional[logging.Logger] = None
    scraper_fn: Callable[..., ReviewDict] = scrape_review
    classifier_fn: Callable[[ReviewDict], float] = predict_review_freshness
    rt_baseline_fetcher: Callable[[str, Optional[str]], Dict[str, Any]] = fetch_rt_title_baseline
    rt_title_path: Optional[str] = None
    seen_review_urls: set[str] = field(default_factory=set)
    accepted_reviews: List[ReviewDict] = field(default_factory=list)
    rejected_events: List[ReviewDict] = field(default_factory=list)
    startup_backfill_complete: bool = False
    rt_baseline: Dict[str, Any] = field(default_factory=dict)
    runtime_view: Optional[RegistryView] = None
    _decision_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.runtime_view is None:
            self.runtime_view = load_runtime_view(self.publication_registry_path, self.source_rules_path)
        if self.monitor is None:
            self.monitor = ReviewDropMonitor(
                publication_registry_path=self.publication_registry_path,
                source_rules_path=self.source_rules_path,
                include_disabled=self.include_disabled,
                publication_ids=self.publication_ids,
                poll_workers=self.poll_workers,
                logger=self.logger,
                runtime_view=self.runtime_view,
            )
        if self.discoverer is None:
            self.discoverer = ReviewDiscoverer(
                publication_registry_path=self.publication_registry_path,
                source_rules_path=self.source_rules_path,
                include_disabled=self.include_disabled,
                runtime_view=self.runtime_view,
            )
        if self.title_search_backfiller is None:
            self.title_search_backfiller = TitleSearchBackfiller(
                publication_registry_path=self.publication_registry_path,
                source_rules_path=self.source_rules_path,
                include_disabled=self.include_disabled,
                runtime_view=self.runtime_view,
            )
        if self.state_store is None:
            self.state_store = FileSystemRealtimeStateStore()
        self._hydrate_from_store()
        if self.logger:
            self.logger.info(
                "engine_initialized title=%s system_reviews=%s seen_urls=%s startup_backfill_complete=%s",
                self.target_title,
                len(self.accepted_reviews),
                len(self.seen_review_urls),
                self.startup_backfill_complete,
            )

    def backfill_existing_reviews(
        self,
        max_publications: Optional[int] = None,
        max_urls_per_publication: int = 12,
        publication_workers: int = 16,
        scrape_workers: int = 24,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        self._emit_progress(progress_callback, phase="backfill_start", completed=0, total=max_publications or 0)
        if self.logger:
            self.logger.info(
                "backfill_start title=%s max_publications=%s max_urls_per_publication=%s publication_workers=%s scrape_workers=%s",
                self.target_title,
                max_publications,
                max_urls_per_publication,
                publication_workers,
                scrape_workers,
            )
        accepted = 0
        recent_result = self.discoverer.discover_with_metadata(
            title=self.target_title,
            max_publications=max_publications,
            max_urls_per_publication=max_urls_per_publication,
            publication_workers=publication_workers,
            scrape_workers=scrape_workers,
            min_confidence=self.min_title_confidence,
            min_review_likeness=self.min_review_likeness,
            publication_ids=self.publication_ids,
            progress_callback=lambda payload: self._emit_progress(progress_callback, **payload),
        )
        search_result = self.title_search_backfiller.search(
            title=self.target_title,
            max_publications=max_publications,
            publication_workers=publication_workers,
            scrape_workers=scrape_workers,
            min_confidence=self.min_title_confidence,
            min_review_likeness=self.min_review_likeness,
            publication_ids=self.publication_ids,
            progress_callback=lambda payload: self._emit_progress(progress_callback, **payload),
        )
        discovered_by_url: Dict[str, Dict[str, Any]] = {}
        for item in recent_result["results"] + search_result["results"]:
            if item.get("url"):
                discovered_by_url[item["url"]] = item
        discovered = list(discovered_by_url.values())
        accepted = self._process_events_parallel(
            [
                {
                    "publication_id": item["publication_id"],
                    "outlet_name": item.get("outlet_name"),
                    "url": item["url"],
                    "event_type": "startup_backfill_candidate",
                }
                for item in discovered
            ],
            progress_callback=progress_callback,
            phase="backfill_processing",
        )
        self.startup_backfill_complete = True
        snapshot = self.snapshot()
        snapshot["accepted_in_backfill"] = accepted
        snapshot["discovered_in_backfill"] = len(discovered)
        snapshot["backfill_recent_publication_attempts"] = recent_result["publication_attempts"]
        snapshot["backfill_recent_publications_with_urls"] = recent_result["publications_with_urls"]
        snapshot["backfill_recent_publications_with_matches"] = recent_result["publications_with_matches"]
        snapshot["backfill_recent_candidate_url_count"] = recent_result["candidate_url_count"]
        snapshot["backfill_title_search_publication_attempts"] = search_result["publication_attempts"]
        snapshot["backfill_title_search_publications_with_search_pages"] = search_result["publications_with_search_pages"]
        snapshot["backfill_title_search_publications_with_candidates"] = search_result["publications_with_candidates"]
        snapshot["backfill_title_search_candidate_url_count"] = search_result["candidate_url_count"]
        snapshot["backfill_candidate_url_count"] = recent_result["candidate_url_count"] + search_result["candidate_url_count"]
        if self.logger:
            self.logger.info(
                "backfill_complete title=%s discovered=%s accepted=%s review_count=%s recent_publication_attempts=%s recent_publications_with_urls=%s recent_publications_with_matches=%s recent_candidate_url_count=%s title_search_publication_attempts=%s title_search_publications_with_search_pages=%s title_search_publications_with_candidates=%s title_search_candidate_url_count=%s",
                self.target_title,
                len(discovered),
                accepted,
                snapshot["review_count"],
                recent_result["publication_attempts"],
                recent_result["publications_with_urls"],
                recent_result["publications_with_matches"],
                recent_result["candidate_url_count"],
                search_result["publication_attempts"],
                search_result["publications_with_search_pages"],
                search_result["publications_with_candidates"],
                search_result["candidate_url_count"],
            )
        self._persist_snapshot(snapshot, event_type="startup_backfill_completed")
        self._emit_progress(
            progress_callback,
            phase="backfill_complete",
            completed=len(discovered),
            total=len(discovered),
            accepted=accepted,
        )
        return snapshot

    def sync_rt_baseline(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        self._emit_progress(progress_callback, phase="rt_sync", completed=0, total=1)
        if self.logger:
            self.logger.info("rt_sync_start title=%s rt_title_path=%s", self.target_title, self.rt_title_path)
        try:
            baseline = self.rt_baseline_fetcher(self.target_title, self.rt_title_path)
        except Exception as exc:
            self.rt_baseline = {
                "available": False,
                "target_title": self.target_title,
                "rt_title_path": self.rt_title_path,
                "review_count": None,
                "tomatometer": None,
                "diagnostics": {
                    "message": f"RT sync crashed: {exc}",
                },
            }
            self.state_store.append_engine_event(
                self.target_title,
                {
                    "event_type": "rt_baseline_sync_failed",
                    "error": str(exc),
                },
            )
            snapshot = self.snapshot()
            if self.logger:
                self.logger.exception("rt_sync_crashed title=%s", self.target_title)
            self._persist_snapshot(snapshot, event_type="rt_baseline_sync_failed")
            self._emit_progress(progress_callback, phase="rt_sync_failed", completed=1, total=1, message=str(exc))
            return snapshot

        if baseline:
            self.rt_baseline = dict(baseline)
            self.rt_title_path = baseline.get("rt_title_path") or self.rt_title_path
            self.state_store.append_engine_event(
                self.target_title,
                {
                    "event_type": "rt_baseline_synced" if baseline.get("available") else "rt_baseline_sync_incomplete",
                    "review_count": baseline.get("review_count"),
                    "tomatometer": baseline.get("tomatometer"),
                    "rt_title_path": baseline.get("rt_title_path"),
                    "diagnostics": baseline.get("diagnostics", {}),
                },
            )
            snapshot = self.snapshot()
            if self.logger:
                self.logger.info(
                    "rt_sync_complete title=%s available=%s review_count=%s tomatometer=%s diagnostics=%s",
                    self.target_title,
                    baseline.get("available"),
                    baseline.get("review_count"),
                    baseline.get("tomatometer"),
                    baseline.get("diagnostics", {}),
                )
            self._persist_snapshot(snapshot, event_type="rt_baseline_sync_completed")
            self._emit_progress(progress_callback, phase="rt_sync_complete", completed=1, total=1)
            return snapshot
        snapshot = self.snapshot()
        if self.logger:
            self.logger.warning("rt_sync_complete title=%s baseline_empty=true", self.target_title)
        self._persist_snapshot(snapshot, event_type="rt_baseline_sync_completed")
        self._emit_progress(progress_callback, phase="rt_sync_complete", completed=1, total=1)
        return snapshot

    def poll_once(
        self,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_events: Optional[int] = None,
    ) -> Dict[str, Any]:
        if self.logger:
            self.logger.info("poll_cycle_start title=%s", self.target_title)
        poll_result = self.monitor.poll_review_sources_with_metadata(
            progress_callback=lambda payload: self._emit_progress(progress_callback, **payload),
            max_events=max_events,
        )
        self.state_store.append_engine_event(
            self.target_title,
            {
                "event_type": "poll_discovery_completed",
                "discovered_url_count": len(poll_result["events"]),
                "total_candidate_event_count": poll_result.get("total_candidate_event_count"),
                "scraper_count": poll_result["scraper_count"],
                "scraper_failures": poll_result["scraper_failures"],
            },
        )
        accepted = self._process_events_parallel(poll_result["events"], progress_callback=progress_callback)
        snapshot = self.snapshot()
        snapshot["accepted_this_poll"] = accepted
        snapshot["discovered_url_count"] = len(poll_result["events"])
        snapshot["total_candidate_event_count"] = poll_result.get("total_candidate_event_count", len(poll_result["events"]))
        snapshot["scraper_count"] = poll_result["scraper_count"]
        snapshot["scraper_failures"] = poll_result["scraper_failures"]
        snapshot["skipped_scrapers"] = poll_result.get("skipped_scrapers", 0)
        if self.logger:
            self.logger.info(
                "poll_cycle_complete title=%s discovered=%s accepted=%s rejected_total=%s review_count=%s",
                self.target_title,
                len(poll_result["events"]),
                accepted,
                len(self.rejected_events),
                snapshot["review_count"],
            )
        self._persist_snapshot(snapshot, event_type="poll_completed")
        self._emit_progress(
            progress_callback,
            phase="poll_complete",
            completed=len(poll_result["events"]),
            total=len(poll_result["events"]),
            accepted=accepted,
        )
        return snapshot

    def watch(
        self,
        iterations: Optional[int] = None,
        sleep_seconds: Optional[int] = None,
        clean_output: bool = False,
    ) -> None:
        poll_interval = RT_POLL_INTERVAL_SECONDS if sleep_seconds is None else sleep_seconds
        completed = 0
        while iterations is None or completed < iterations:
            snapshot = self.poll_once()
            print(format_clean_snapshot(snapshot) if clean_output else snapshot)
            completed += 1
            if iterations is not None and completed >= iterations:
                break
            time.sleep(poll_interval)

    def snapshot(self) -> Dict[str, Any]:
        review_count = len(self.accepted_reviews)
        expected_fresh_reviews = sum(float(review["fresh_probability"]) for review in self.accepted_reviews)
        expected_rotten_reviews = max(0.0, review_count - expected_fresh_reviews)
        binary_fresh_reviews = sum(1 for review in self.accepted_reviews if float(review["fresh_probability"]) >= self.fresh_cutoff)
        binary_rotten_reviews = max(0, review_count - binary_fresh_reviews)
        calculated_tomatometer = round((expected_fresh_reviews / review_count) * 100.0, 2) if review_count else None
        binary_tomatometer = round((binary_fresh_reviews / review_count) * 100.0, 2) if review_count else None

        return {
            "target_title": self.target_title,
            "review_count": review_count,
            "system_review_count": review_count,
            "expected_fresh_reviews": round(expected_fresh_reviews, 4),
            "expected_rotten_reviews": round(expected_rotten_reviews, 4),
            "calculated_tomatometer": calculated_tomatometer,
            "binary_fresh_reviews": binary_fresh_reviews,
            "binary_rotten_reviews": binary_rotten_reviews,
            "binary_tomatometer": binary_tomatometer,
            "official_rt_review_count": self.rt_baseline.get("review_count"),
            "official_rt_tomatometer": self.rt_baseline.get("tomatometer"),
            "official_rt_title_path": self.rt_baseline.get("rt_title_path"),
            "official_rt_diagnostics": self.rt_baseline.get("diagnostics", {}),
            "latest_reviews": self.accepted_reviews[-5:],
            "rejected_event_count": len(self.rejected_events),
            "startup_backfill_complete": self.startup_backfill_complete,
        }

    def _process_event(self, event: Dict[str, Any]) -> bool:
        decision = self._safe_evaluate_event(event)
        return self._apply_event_decision(decision)

    def _safe_evaluate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self._evaluate_event(event)
        except Exception as exc:
            if self.logger:
                self.logger.exception("event_processing_failed url=%s", event.get("url"))
            return {
                "status": "rejected", "event": event, "url": event.get("url"),
                "canonical_url": event.get("url"), "reason": "processing_failed",
                "details": {"error": str(exc)}, "retryable": True,
            }

    def _evaluate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        url = event.get("url")
        if not url or url in self.seen_review_urls:
            if self.logger and url:
                self.logger.debug("event_ignored_seen_url title=%s url=%s", self.target_title, url)
            return {"status": "ignored", "event": event, "url": url}

        try:
            record = self.scraper_fn(
                url,
                event["publication_id"],
                publication_registry_path=self.publication_registry_path,
                source_rules_path=self.source_rules_path,
                include_disabled=self.include_disabled,
                runtime_view=self.runtime_view,
            )
        except Exception as exc:
            if self.logger:
                self.logger.warning(
                    "event_scrape_failed title=%s publication_id=%s url=%s error=%s",
                    self.target_title,
                    event.get("publication_id"),
                    url,
                    exc,
                )
            return {
                "status": "rejected",
                "event": event,
                "url": url,
                "canonical_url": url,
                "reason": "scrape_failed",
                "details": {"error": str(exc)},
                "retryable": True,
            }

        canonical_url = record.get("canonical_url") or record.get("source_url") or url
        if canonical_url in self.seen_review_urls:
            if self.logger:
                self.logger.debug("event_ignored_seen_canonical title=%s url=%s canonical_url=%s", self.target_title, url, canonical_url)
            return {"status": "ignored", "event": event, "url": url, "canonical_url": canonical_url}

        review_meta = classify_review_candidate(record)
        if review_meta["review_likeness"] < self.min_review_likeness:
            if self.logger:
                self.logger.info(
                    "event_rejected_review_likeness title=%s publication_id=%s url=%s review_likeness=%s",
                    self.target_title,
                    event.get("publication_id"),
                    canonical_url,
                    review_meta["review_likeness"],
                )
            return {
                "status": "rejected",
                "event": event,
                "url": url,
                "canonical_url": canonical_url,
                "reason": "low_review_likeness",
                "details": review_meta,
                "retryable": False,
            }

        candidate_options = [
            value
            for value in [
                record.get("headline"),
                record.get("canonical_url"),
                record.get("source_url"),
            ]
            if value
        ]
        title_match = match_title(self.target_title, candidate_options)
        if float(title_match["confidence"]) < self.min_title_confidence:
            if self.logger:
                self.logger.info(
                    "event_rejected_title_confidence title=%s publication_id=%s url=%s confidence=%s",
                    self.target_title,
                    event.get("publication_id"),
                    canonical_url,
                    title_match["confidence"],
                )
            return {
                "status": "rejected",
                "event": event,
                "url": url,
                "canonical_url": canonical_url,
                "reason": "low_title_confidence",
                "details": title_match,
                "retryable": False,
            }

        fresh_probability = float(self.classifier_fn(record))
        if not math.isfinite(fresh_probability) or not 0.0 <= fresh_probability <= 1.0:
            raise ValueError("Fresh probability must be finite and between 0 and 1")
        seen_url_aliases = sorted({str(value) for value in [url, canonical_url, record.get("source_url")] if value})
        accepted_record = {
            "publication_id": event["publication_id"],
            "outlet_name": event.get("outlet_name"),
            "url": canonical_url,
            "source_url": url,
            "headline": record.get("headline"),
            "published_at": record.get("published_at"),
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "critic_name": record.get("critic_name"),
            "raw_score": record.get("raw_score"),
            "fresh_probability": round(fresh_probability, 4),
            "fresh_label_estimate": int(fresh_probability >= self.fresh_cutoff),
            "match_confidence": float(title_match["confidence"]),
            "review_likeness": float(review_meta["review_likeness"]),
            "seen_url_aliases": seen_url_aliases,
        }
        return {
            "status": "accepted",
            "event": event,
            "url": url,
            "canonical_url": canonical_url,
            "accepted_record": accepted_record,
        }

    def _process_events_parallel(
        self,
        events: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        phase: str = "poll_processing",
    ) -> int:
        if not events:
            return 0
        deduplicated_events = self._deduplicate_incoming_events(events)
        decisions: List[Dict[str, Any]] = []
        completed = 0
        self._emit_progress(progress_callback, phase=phase, completed=0, total=len(deduplicated_events), accepted=0)
        with ThreadPoolExecutor(max_workers=min(self.process_workers, max(1, len(deduplicated_events)))) as executor:
            future_map = {
                executor.submit(self._safe_evaluate_event, event): event
                for event in deduplicated_events
            }
            for future in as_completed(future_map):
                decisions.append(future.result())
                completed += 1
                self._emit_progress(
                    progress_callback,
                    phase=phase,
                    completed=completed,
                    total=len(deduplicated_events),
                )

        decisions.sort(key=lambda item: (str(item.get("canonical_url") or item.get("url") or ""), str(item.get("status") or "")))
        accepted = 0
        for index, decision in enumerate(decisions, start=1):
            if self._apply_event_decision(decision):
                accepted += 1
            self._emit_progress(
                progress_callback,
                phase=phase,
                completed=index,
                total=len(deduplicated_events),
                accepted=accepted,
            )
        return accepted

    def _apply_event_decision(self, decision: Dict[str, Any]) -> bool:
        status = decision.get("status")
        if status == "ignored":
            return False
        if status == "rejected":
            canonical_url = decision.get("canonical_url") or decision.get("url")
            retryable = bool(decision.get("retryable", False))
            self._reject_event(
                decision["event"],
                str(canonical_url),
                reason=str(decision["reason"]),
                extra=decision.get("details", {}),
                retryable=retryable,
            )
            if canonical_url and not retryable:
                self._acknowledge_urls({str(canonical_url), str(decision.get("url") or canonical_url)})
            return False
        if status != "accepted":
            return False

        accepted_record = dict(decision["accepted_record"])
        canonical_url = str(decision.get("canonical_url") or accepted_record.get("url"))
        with self._decision_lock:
            if canonical_url in self.seen_review_urls:
                return False
            self.state_store.append_engine_event(
                self.target_title,
                {
                    "event_type": "review_accepted",
                    "publication_id": decision["event"]["publication_id"],
                    "url": canonical_url,
                    "source_url": decision.get("url"),
                    "fresh_probability": accepted_record["fresh_probability"],
                    "accepted_record": accepted_record,
                },
            )
            self.state_store.append_accepted_review(self.target_title, accepted_record)
            self.accepted_reviews.append(accepted_record)
            self._acknowledge_urls(self._seen_aliases_for_payload(accepted_record))
        if self.logger:
            self.logger.info(
                "event_accepted title=%s publication_id=%s url=%s fresh_probability=%s",
                self.target_title,
                decision["event"]["publication_id"],
                canonical_url,
                accepted_record["fresh_probability"],
            )
        return True

    def _acknowledge_urls(self, urls: set[str]) -> None:
        self.seen_review_urls.update(urls)
        if hasattr(self.monitor, "acknowledge_urls"):
            self.monitor.acknowledge_urls(urls)
        elif hasattr(self.monitor, "seen_urls"):
            self.monitor.seen_urls.update(urls)

    def _reject_event(
        self,
        event: Dict[str, Any],
        canonical_url: str,
        reason: str,
        extra: Dict[str, Any],
        retryable: bool,
    ) -> None:
        rejected = {
            "publication_id": event.get("publication_id"),
            "url": canonical_url,
            "source_url": event.get("url"),
            "reason": reason,
            "details": extra,
            "retryable": retryable,
        }
        self.rejected_events.append(rejected)
        self.state_store.append_engine_event(
            self.target_title,
            {
                "event_type": "review_rejected",
                "publication_id": event.get("publication_id"),
                "url": canonical_url,
                "source_url": event.get("url"),
                "reason": reason,
                "retryable": retryable,
                "rejected_record": rejected,
            },
        )
        self.state_store.append_rejected_event(self.target_title, rejected)
        if self.logger:
            self.logger.info(
                "event_rejected title=%s publication_id=%s url=%s reason=%s retryable=%s details=%s",
                self.target_title,
                event.get("publication_id"),
                canonical_url,
                reason,
                retryable,
                extra,
            )

    def _hydrate_from_store(self) -> None:
        runtime_state = self.state_store.load_runtime_state(self.target_title)
        self.accepted_reviews = list(runtime_state.accepted_reviews)
        self.rejected_events = list(runtime_state.rejected_events)
        self.seen_review_urls = set(runtime_state.seen_review_urls)
        self.startup_backfill_complete = runtime_state.startup_backfill_complete
        self.rt_baseline = dict(runtime_state.rt_baseline)
        if hasattr(self.monitor, "seen_urls"):
            self.monitor.seen_urls.update(self.seen_review_urls)

    def _deduplicate_incoming_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduplicated: List[Dict[str, Any]] = []
        seen_urls: set[str] = set()
        for event in events:
            url = str(event.get("url") or "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deduplicated.append(event)
        return deduplicated

    def _seen_aliases_for_payload(self, payload: Dict[str, Any]) -> set[str]:
        aliases: set[str] = set()
        for key in ("url", "canonical_url", "source_url"):
            value = payload.get(key)
            if value:
                aliases.add(str(value))
        for alias in payload.get("seen_url_aliases", []):
            if alias:
                aliases.add(str(alias))
        return aliases

    def _persist_snapshot(self, snapshot: Dict[str, Any], event_type: str) -> None:
        self.state_store.persist_snapshot(
            self.target_title,
            snapshot,
            startup_backfill_complete=self.startup_backfill_complete,
            seen_review_urls=self.seen_review_urls,
            rt_baseline=self.rt_baseline,
        )
        self.state_store.append_engine_event(
            self.target_title,
            {
                "event_type": event_type,
                "review_count": snapshot["review_count"],
                "calculated_tomatometer": snapshot["calculated_tomatometer"],
            },
        )

    def _emit_progress(
        self,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]],
        **payload: Any,
    ) -> None:
        if not progress_callback:
            return
        progress_payload = {"target_title": self.target_title}
        progress_payload.update(payload)
        progress_callback(progress_payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll critic sites and maintain a live calculated Tomatometer for one title.")
    parser.add_argument("title", type=str, help="Film title to track")
    parser.add_argument("--publication-id", action="append", dest="publication_ids")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--continuous", action="store_true", help="Poll until interrupted")
    parser.add_argument("--sleep-seconds", type=int, default=RT_POLL_INTERVAL_SECONDS)
    parser.add_argument("--min-title-confidence", type=float, default=0.6)
    parser.add_argument("--min-review-likeness", type=float, default=0.45)
    parser.add_argument("--skip-backfill", action="store_true")
    parser.add_argument("--backfill-max-publications", type=int, default=None)
    parser.add_argument("--backfill-max-urls-per-publication", type=int, default=20)
    parser.add_argument("--backfill-publication-workers", type=int, default=16)
    parser.add_argument("--backfill-scrape-workers", type=int, default=24)
    parser.add_argument("--poll-workers", type=int, default=DEFAULT_POLL_WORKERS)
    parser.add_argument("--process-workers", type=int, default=DEFAULT_POLL_WORKERS)
    parser.add_argument("--rt-title-path", type=str, default=None)
    parser.add_argument("--skip-rt-sync", action="store_true")
    parser.add_argument("--state-root", type=str, default="data/live")
    parser.add_argument("--reset-state", action="store_true", help="Delete the persisted state for this title before starting")
    parser.add_argument("--log-file", type=str, default=None)
    parser.add_argument("--log-level", type=str, default="INFO")
    parser.add_argument("--clean", action="store_true", help="Print compact live score updates instead of full snapshots")
    args = parser.parse_args()
    if args.iterations < 0 or args.sleep_seconds <= 0:
        parser.error("iterations must be nonnegative and sleep-seconds must be positive")
    if min(args.poll_workers, args.process_workers, args.backfill_publication_workers, args.backfill_scrape_workers) < 1:
        parser.error("worker counts must be positive")

    state_store = FileSystemRealtimeStateStore(root_dir=args.state_root)
    if args.reset_state:
        state_store.delete_title_state(args.title)
    title_slug = Path(args.state_root) / slugify_title(args.title)
    log_file = args.log_file or str(title_slug / "runtime.log")
    logger = configure_file_logger("rtKalshiPred.runtime", log_file, level=args.log_level)

    engine = RealtimeTomatometerEngine(
        target_title=args.title,
        publication_ids=args.publication_ids,
        min_title_confidence=args.min_title_confidence,
        min_review_likeness=args.min_review_likeness,
        poll_workers=args.poll_workers,
        process_workers=args.process_workers,
        rt_title_path=args.rt_title_path,
        state_store=state_store,
        logger=logger,
    )
    initial_snapshot = engine.snapshot()
    if args.clean:
        print(format_status_message(args.title, "Loaded existing state."))
        print(format_clean_snapshot(initial_snapshot, phase="startup"))
    else:
        print("Loaded existing state:")
        print(initial_snapshot)
    if not args.skip_rt_sync:
        if args.clean:
            print(format_status_message(args.title, "Syncing official Rotten Tomatoes baseline..."))
        else:
            print("Syncing official Rotten Tomatoes baseline...")
        rt_snapshot = engine.sync_rt_baseline()
        print(format_clean_snapshot(rt_snapshot, phase="startup") if args.clean else rt_snapshot)
    if not args.skip_backfill:
        if args.clean:
            print(format_status_message(args.title, "Starting startup backfill across configured publications..."))
        else:
            print("Starting startup backfill across configured publications...")
        backfill_snapshot = engine.backfill_existing_reviews(
                max_publications=args.backfill_max_publications,
                max_urls_per_publication=args.backfill_max_urls_per_publication,
                publication_workers=args.backfill_publication_workers,
                scrape_workers=args.backfill_scrape_workers,
            )
        print(format_clean_snapshot(backfill_snapshot, phase="backfill") if args.clean else backfill_snapshot)
        if args.clean:
            print(
                format_completion_message(
                    args.title,
                    "Backfill complete",
                    "recent_publication_attempts={0}, recent_candidate_urls={1}, title_search_publication_attempts={2}, title_search_candidate_urls={3}, accepted={4}".format(
                        backfill_snapshot.get("backfill_recent_publication_attempts", 0),
                        backfill_snapshot.get("backfill_recent_candidate_url_count", 0),
                        backfill_snapshot.get("backfill_title_search_publication_attempts", 0),
                        backfill_snapshot.get("backfill_title_search_candidate_url_count", 0),
                        backfill_snapshot.get("accepted_in_backfill", 0),
                    ),
                )
            )
    engine.watch(iterations=None if args.continuous else args.iterations, sleep_seconds=args.sleep_seconds, clean_output=args.clean)


if __name__ == "__main__":
    main()

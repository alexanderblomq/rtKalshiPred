from realtime_tomatometer import (
    RealtimeTomatometerEngine,
    format_clean_snapshot,
    format_completion_message,
    format_health_report,
    format_status_message,
)
from state_store import FileSystemRealtimeStateStore


class FakeMonitor:
    def __init__(self, polls):
        self.polls = list(polls)
        self.seen_urls = set()

    def poll_review_sources(self):
        if not self.polls:
            return []
        return self.polls.pop(0)

    def poll_review_sources_with_metadata(self, progress_callback=None, max_events=None):
        events = self.poll_review_sources()
        if max_events is not None:
            events = events[:max_events]
        if progress_callback is not None:
            progress_callback(
                {
                    "phase": "poll_discovery",
                    "completed": len(events),
                    "total": len(events),
                    "scraper_failures": 0,
                    "discovered_url_count": len(events),
                }
            )
        return {
            "events": events,
            "scraper_count": len(events),
            "scraper_failures": 0,
            "total_candidate_event_count": len(events),
            "skipped_scrapers": 0,
        }


class FakeDiscoverer:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def discover(self, **kwargs):
        self.calls.append(kwargs)
        return list(self.results)

    def discover_with_metadata(self, **kwargs):
        self.calls.append(kwargs)
        callback = kwargs.get("progress_callback")
        if callback is not None:
            callback(
                {
                    "phase": "backfill_recent_discovery",
                    "completed": 5,
                    "total": 5,
                    "candidate_url_count": 7,
                    "publications_with_urls": 2,
                    "publications_with_matches": 1 if self.results else 0,
                }
            )
        return {
            "results": list(self.results),
            "publication_attempts": 5,
            "publications_with_urls": 2,
            "publications_with_matches": 1 if self.results else 0,
            "candidate_url_count": 7,
        }


class FakeTitleSearchBackfiller:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        callback = kwargs.get("progress_callback")
        if callback is not None:
            callback(
                {
                    "phase": "backfill_title_search",
                    "completed": 4,
                    "total": 4,
                    "candidate_url_count": 3,
                    "publications_with_search_pages": 2,
                    "publications_with_candidates": 1 if self.results else 0,
                }
            )
        return {
            "results": list(self.results),
            "publication_attempts": 4,
            "publications_with_search_pages": 2,
            "publications_with_candidates": 1 if self.results else 0,
            "candidate_url_count": 3,
        }


def _make_store(root_dir):
    return FileSystemRealtimeStateStore(root_dir=str(root_dir))


def test_realtime_tomatometer_updates_internal_score_and_deduplicates(state_store_root):
    polls = [
        [
            {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/review-1"},
            {"publication_id": "pub2", "outlet_name": "Outlet Two", "url": "https://example.com/review-2"},
        ],
        [
            {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/review-1"},
        ],
    ]
    scraped = {
        "https://example.com/review-1": {
            "source_url": "https://example.com/review-1",
            "canonical_url": "https://example.com/review-1",
            "headline": "Animal Farm review: a sharp adaptation",
            "body_text": "This review calls the film strong and effective.",
            "published_at": "2026-04-21T10:00:00Z",
            "raw_score": None,
        },
        "https://example.com/review-2": {
            "source_url": "https://example.com/review-2",
            "canonical_url": "https://example.com/review-2",
            "headline": "Animal Farm reviewed: a clumsy retelling",
            "body_text": "A disappointing and weak film.",
            "published_at": "2026-04-21T10:01:00Z",
            "raw_score": None,
        },
    }
    probs = {
        "https://example.com/review-1": 0.85,
        "https://example.com/review-2": 0.20,
    }

    def fake_scraper(url, publication_id, **kwargs):
        return scraped[url]

    def fake_classifier(record):
        return probs[record["canonical_url"]]

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor(polls),
        scraper_fn=fake_scraper,
        classifier_fn=fake_classifier,
        state_store=_make_store(state_store_root),
        process_workers=2,
    )

    first = engine.poll_once()
    second = engine.poll_once()

    assert first["accepted_this_poll"] == 2
    assert second["accepted_this_poll"] == 0
    assert first["review_count"] == 2
    assert first["calculated_tomatometer"] == 52.5
    assert first["binary_tomatometer"] == 50.0
    assert engine.snapshot()["expected_fresh_reviews"] == 1.05


def test_realtime_tomatometer_backfills_existing_reviews_before_polling(state_store_root):
    discoverer = FakeDiscoverer(
        [
            {
                "publication_id": "pub1",
                "outlet_name": "Outlet One",
                "url": "https://example.com/review-1",
            },
            {
                "publication_id": "pub2",
                "outlet_name": "Outlet Two",
                "url": "https://example.com/review-2",
            },
        ]
    )
    scraped = {
        "https://example.com/review-1": {
            "source_url": "https://example.com/review-1",
            "canonical_url": "https://example.com/review-1",
            "headline": "Animal Farm review: a sharp adaptation",
            "body_text": "This review calls the film strong and effective.",
            "published_at": "2026-04-21T10:00:00Z",
            "raw_score": None,
        },
        "https://example.com/review-2": {
            "source_url": "https://example.com/review-2",
            "canonical_url": "https://example.com/review-2",
            "headline": "Animal Farm reviewed: a clumsy retelling",
            "body_text": "A disappointing and weak film.",
            "published_at": "2026-04-21T10:01:00Z",
            "raw_score": None,
        },
    }
    probs = {
        "https://example.com/review-1": 0.85,
        "https://example.com/review-2": 0.20,
    }

    def fake_scraper(url, publication_id, **kwargs):
        return scraped[url]

    def fake_classifier(record):
        return probs[record["canonical_url"]]

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor([[]]),
        discoverer=discoverer,
        title_search_backfiller=FakeTitleSearchBackfiller([]),
        scraper_fn=fake_scraper,
        classifier_fn=fake_classifier,
        publication_ids=["pub1", "pub2"],
        state_store=_make_store(state_store_root),
        process_workers=2,
    )

    snapshot = engine.backfill_existing_reviews(max_publications=25, max_urls_per_publication=5)

    assert snapshot["accepted_in_backfill"] == 2
    assert snapshot["discovered_in_backfill"] == 2
    assert snapshot["review_count"] == 2
    assert snapshot["calculated_tomatometer"] == 52.5
    assert snapshot["startup_backfill_complete"] is True
    assert discoverer.calls[0]["publication_ids"] == ["pub1", "pub2"]
    assert discoverer.calls[0]["max_publications"] == 25


def test_realtime_tomatometer_rejects_unrelated_or_non_review_pages(state_store_root):
    polls = [[
        {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/newsletter"},
        {"publication_id": "pub2", "outlet_name": "Outlet Two", "url": "https://example.com/other-movie"},
    ]]
    scraped = {
        "https://example.com/newsletter": {
            "source_url": "https://example.com/newsletter",
            "canonical_url": "https://example.com/newsletter",
            "headline": "ISSUE #119",
            "body_text": "Welcome back to our newsletter." * 20,
            "published_at": "2026-04-21T10:00:00Z",
            "raw_score": None,
        },
        "https://example.com/other-movie": {
            "source_url": "https://example.com/other-movie",
            "canonical_url": "https://example.com/other-movie",
            "headline": "The Brutalist review",
            "body_text": "A strong and moving film.",
            "published_at": "2026-04-21T10:01:00Z",
            "raw_score": None,
        },
    }

    def fake_scraper(url, publication_id, **kwargs):
        return scraped[url]

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor(polls),
        scraper_fn=fake_scraper,
        classifier_fn=lambda record: 0.9,
        state_store=_make_store(state_store_root),
        process_workers=2,
    )

    snapshot = engine.poll_once()

    assert snapshot["review_count"] == 0
    assert snapshot["calculated_tomatometer"] is None
    assert snapshot["rejected_event_count"] == 2


def test_realtime_tomatometer_rejects_scrape_failures_without_crashing(state_store_root):
    polls = [[
        {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/bad"},
    ]]

    def failing_scraper(url, publication_id, **kwargs):
        raise RuntimeError("network error")

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor(polls),
        scraper_fn=failing_scraper,
        classifier_fn=lambda record: 0.9,
        state_store=_make_store(state_store_root),
        process_workers=2,
    )

    snapshot = engine.poll_once()

    assert snapshot["review_count"] == 0
    assert snapshot["rejected_event_count"] == 1


def test_realtime_tomatometer_backfill_deduplicates_against_later_live_poll(state_store_root):
    discoverer = FakeDiscoverer(
        [
            {
                "publication_id": "pub1",
                "outlet_name": "Outlet One",
                "url": "https://example.com/review-1",
            }
        ]
    )
    polls = [[
        {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/review-1"},
    ]]
    scraped = {
        "https://example.com/review-1": {
            "source_url": "https://example.com/review-1",
            "canonical_url": "https://example.com/review-1",
            "headline": "Animal Farm review: a sharp adaptation",
            "body_text": "This review calls the film strong and effective.",
            "published_at": "2026-04-21T10:00:00Z",
            "raw_score": None,
        }
    }

    def fake_scraper(url, publication_id, **kwargs):
        return scraped[url]

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor(polls),
        discoverer=discoverer,
        title_search_backfiller=FakeTitleSearchBackfiller([]),
        scraper_fn=fake_scraper,
        classifier_fn=lambda record: 0.85,
        state_store=_make_store(state_store_root),
        process_workers=2,
    )

    backfill = engine.backfill_existing_reviews()
    poll = engine.poll_once()

    assert backfill["review_count"] == 1
    assert poll["accepted_this_poll"] == 0
    assert poll["review_count"] == 1


def test_realtime_tomatometer_recovers_persisted_state_after_restart(state_store_root):
    store = _make_store(state_store_root)
    polls = [[
        {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/review-1"},
    ]]
    scraped = {
        "https://example.com/review-1": {
            "source_url": "https://example.com/review-1",
            "canonical_url": "https://example.com/review-1",
            "headline": "Animal Farm review: a sharp adaptation",
            "body_text": "This review calls the film strong and effective.",
            "published_at": "2026-04-21T10:00:00Z",
            "raw_score": None,
        }
    }

    def fake_scraper(url, publication_id, **kwargs):
        return scraped[url]

    first_engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor(polls),
        scraper_fn=fake_scraper,
        classifier_fn=lambda record: 0.85,
        state_store=store,
    )
    first_snapshot = first_engine.poll_once()

    second_engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor([[{"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/review-1"}]]),
        scraper_fn=fake_scraper,
        classifier_fn=lambda record: 0.85,
        state_store=store,
    )
    second_snapshot = second_engine.poll_once()

    assert first_snapshot["review_count"] == 1
    assert second_snapshot["review_count"] == 1
    assert second_snapshot["accepted_this_poll"] == 0


def test_realtime_tomatometer_hydrates_monitor_seen_urls_from_state_store(state_store_root):
    store = _make_store(state_store_root)
    store.persist_snapshot(
        "Animal Farm",
        snapshot={"review_count": 0, "calculated_tomatometer": None},
        startup_backfill_complete=False,
        seen_review_urls={"https://example.com/review-1"},
        rt_baseline={},
    )
    monitor = FakeMonitor([[]])
    monitor.seen_urls = set()

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=monitor,
        state_store=store,
    )

    assert "https://example.com/review-1" in monitor.seen_urls


def test_format_clean_snapshot_uses_compact_console_layout():
    rendered = format_clean_snapshot(
        {
            "target_title": "Animal Farm",
            "review_count": 3,
            "system_review_count": 3,
            "accepted_this_poll": 1,
            "calculated_tomatometer": 61.67,
            "official_rt_review_count": 5,
            "official_rt_tomatometer": 80.0,
            "official_rt_diagnostics": {},
            "latest_reviews": [
                {
                    "outlet_name": "Variety",
                    "headline": "Animal Farm review: a sharp adaptation",
                    "fresh_probability": 0.82,
                }
            ],
        }
    )

    assert "Animal Farm" in rendered
    assert "Predicted RT: 61.67%" in rendered
    assert "System Reviews: 3" in rendered
    assert "Official RT Reviews: 5" in rendered
    assert "Official RT Score: 80%" in rendered
    assert "New This Cycle: 1" in rendered
    assert "Latest: Variety | 82.0% fresh | Animal Farm review: a sharp adaptation" in rendered


def test_format_clean_snapshot_includes_rt_sync_diagnostics():
    rendered = format_clean_snapshot(
        {
            "target_title": "Wuthering Heights",
            "system_review_count": 0,
            "accepted_this_poll": 0,
            "calculated_tomatometer": None,
            "official_rt_review_count": None,
            "official_rt_tomatometer": None,
            "official_rt_diagnostics": {"message": "Fetch failed: blocked"},
            "latest_reviews": [],
        }
    )

    assert "RT Sync: Fetch failed: blocked" in rendered


def test_format_status_message_renders_title_and_status_line():
    rendered = format_status_message("Animal Farm", "Starting startup backfill across configured publications...")

    assert rendered == "Animal Farm\nStarting startup backfill across configured publications..."


def test_format_completion_message_renders_label_and_details():
    rendered = format_completion_message("Animal Farm", "Backfill complete", "accepted=0")

    assert rendered == "Animal Farm\nBackfill complete: accepted=0"


def test_format_health_report_renders_poll_counters():
    rendered = format_health_report(
        {
            "scraper_count": 10,
            "skipped_scrapers": 2,
            "scraper_failures": 8,
            "discovered_url_count": 1,
            "accepted_this_poll": 1,
            "rejected_event_count": 2,
            "official_rt_diagnostics": {"message": "Fetch failed"},
        },
        phase="poll",
    )

    assert "Scrapers attempted: 10" in rendered
    assert "Scrapers skipped (backoff): 2" in rendered
    assert "Scraper failures: 8" in rendered
    assert "Discovered URLs: 1" in rendered
    assert "RT diagnostics: Fetch failed" in rendered


def test_format_health_report_renders_backfill_counters():
    rendered = format_health_report(
        {
            "backfill_recent_publication_attempts": 5,
            "backfill_recent_publications_with_urls": 2,
            "backfill_recent_candidate_url_count": 7,
            "backfill_title_search_publication_attempts": 4,
            "backfill_title_search_publications_with_search_pages": 3,
            "backfill_title_search_candidate_url_count": 6,
            "accepted_in_backfill": 1,
        },
        phase="backfill",
    )

    assert "Recent publication attempts: 5" in rendered
    assert "Title-search candidate URLs: 6" in rendered
    assert "Accepted in backfill: 1" in rendered


def test_realtime_tomatometer_syncs_official_rt_baseline(state_store_root):
    store = _make_store(state_store_root)
    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor([[]]),
        state_store=store,
        rt_baseline_fetcher=lambda title, path: {
            "available": True,
            "review_count": 5,
            "tomatometer": 80.0,
            "rt_title_path": "m/animal_farm_2025",
            "diagnostics": {"fetch_status": "ok", "parse_status": "ok", "message": None},
        },
    )

    snapshot = engine.sync_rt_baseline()

    assert snapshot["official_rt_review_count"] == 5
    assert snapshot["official_rt_tomatometer"] == 80.0
    assert snapshot["official_rt_title_path"] == "m/animal_farm_2025"
    assert snapshot["official_rt_diagnostics"]["fetch_status"] == "ok"


def test_realtime_tomatometer_backfill_records_discovery_metadata(state_store_root):
    discoverer = FakeDiscoverer([])
    title_search = FakeTitleSearchBackfiller([])
    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor([[]]),
        discoverer=discoverer,
        title_search_backfiller=title_search,
        state_store=_make_store(state_store_root),
    )

    snapshot = engine.backfill_existing_reviews()

    assert snapshot["backfill_recent_publication_attempts"] == 5
    assert snapshot["backfill_recent_publications_with_urls"] == 2
    assert snapshot["backfill_recent_publications_with_matches"] == 0
    assert snapshot["backfill_recent_candidate_url_count"] == 7
    assert snapshot["backfill_title_search_publication_attempts"] == 4
    assert snapshot["backfill_title_search_publications_with_search_pages"] == 2
    assert snapshot["backfill_title_search_publications_with_candidates"] == 0
    assert snapshot["backfill_title_search_candidate_url_count"] == 3


def test_realtime_tomatometer_backfill_emits_progress_updates(state_store_root):
    updates = []
    discoverer = FakeDiscoverer([])
    title_search = FakeTitleSearchBackfiller([])
    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor([[]]),
        discoverer=discoverer,
        title_search_backfiller=title_search,
        state_store=_make_store(state_store_root),
    )

    engine.backfill_existing_reviews(progress_callback=updates.append)

    phases = [item["phase"] for item in updates]
    assert "backfill_recent_discovery" in phases
    assert "backfill_title_search" in phases
    assert phases[-1] == "backfill_complete"


def test_realtime_tomatometer_poll_emits_progress_updates(state_store_root):
    updates = []
    polls = [[
        {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/review-1"},
    ]]
    scraped = {
        "https://example.com/review-1": {
            "source_url": "https://example.com/review-1",
            "canonical_url": "https://example.com/review-1",
            "headline": "Animal Farm review: a sharp adaptation",
            "body_text": "This review calls the film strong and effective.",
            "published_at": "2026-04-21T10:00:00Z",
            "raw_score": None,
        }
    }

    def fake_scraper(url, publication_id, **kwargs):
        return scraped[url]

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor(polls),
        scraper_fn=fake_scraper,
        classifier_fn=lambda record: 0.85,
        state_store=_make_store(state_store_root),
        process_workers=2,
    )

    engine.poll_once(progress_callback=updates.append)

    phases = [item["phase"] for item in updates]
    assert "poll_discovery" in phases
    assert "poll_processing" in phases
    assert phases[-1] == "poll_complete"


def test_realtime_tomatometer_poll_records_total_candidate_event_count(state_store_root):
    polls = [[
        {"publication_id": "pub1", "outlet_name": "Outlet One", "url": "https://example.com/review-1"},
    ]]
    scraped = {
        "https://example.com/review-1": {
            "source_url": "https://example.com/review-1",
            "canonical_url": "https://example.com/review-1",
            "headline": "Animal Farm review: a sharp adaptation",
            "body_text": "This review calls the film strong and effective.",
            "published_at": "2026-04-21T10:00:00Z",
            "raw_score": None,
        }
    }

    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor(polls),
        scraper_fn=lambda url, publication_id, **kwargs: scraped[url],
        classifier_fn=lambda record: 0.85,
        state_store=_make_store(state_store_root),
        process_workers=2,
    )

    snapshot = engine.poll_once(max_events=1)

    assert snapshot["discovered_url_count"] == 1
    assert snapshot["total_candidate_event_count"] == 1


def test_realtime_tomatometer_persists_rt_sync_failures_as_snapshot_state(state_store_root):
    store = _make_store(state_store_root)
    engine = RealtimeTomatometerEngine(
        target_title="Animal Farm",
        monitor=FakeMonitor([[]]),
        state_store=store,
        rt_baseline_fetcher=lambda title, path: (_ for _ in ()).throw(RuntimeError("socket denied")),
    )

    snapshot = engine.sync_rt_baseline()
    reloaded = store.load_runtime_state("Animal Farm")

    assert "socket denied" in snapshot["official_rt_diagnostics"]["message"]
    assert "socket denied" in reloaded.rt_baseline["diagnostics"]["message"]

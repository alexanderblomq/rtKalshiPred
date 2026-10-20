from review_drop_monitor import ReviewDropMonitor


class FakeScraper:
    def __init__(self, publication_id: str, outlet_name: str, urls):
        self.publication = type(
            "Publication",
            (),
            {"publication_id": publication_id, "outlet_name": outlet_name},
        )()
        self.source_name = "fake"
        self._urls = urls

    def list_recent_urls(self):
        return list(self._urls)


def test_review_drop_monitor_deduplicates_seen_urls():
    monitor = ReviewDropMonitor()
    fake_scraper = FakeScraper("test_pub", "Test Outlet", ["https://example.com/review/a"])
    monitor.build_scrapers = lambda: [fake_scraper]

    first = monitor.poll_review_sources()
    second = monitor.poll_review_sources()

    assert len(first) == 1
    assert first[0]["publication_id"] == "test_pub"
    assert second == []


def test_review_drop_monitor_skips_failing_scrapers():
    monitor = ReviewDropMonitor()
    good_scraper = FakeScraper("good_pub", "Good Outlet", ["https://example.com/review/a"])

    class FailingScraper(FakeScraper):
        def list_recent_urls(self):
            raise RuntimeError("boom")

    monitor.build_scrapers = lambda: [
        FailingScraper("bad_pub", "Bad Outlet", []),
        good_scraper,
    ]

    events = monitor.poll_review_sources()

    assert len(events) == 1
    assert events[0]["publication_id"] == "good_pub"


def test_review_drop_monitor_returns_metadata_for_parallel_polling():
    monitor = ReviewDropMonitor(poll_workers=4)
    first_scraper = FakeScraper("b_pub", "B Outlet", ["https://example.com/review/b"])
    second_scraper = FakeScraper("a_pub", "A Outlet", ["https://example.com/review/a"])
    monitor.build_scrapers = lambda: [first_scraper, second_scraper]

    result = monitor.poll_review_sources_with_metadata()

    assert result["scraper_count"] == 2
    assert result["scraper_failures"] == 0
    assert [event["publication_id"] for event in result["events"]] == ["a_pub", "b_pub"]


def test_review_drop_monitor_emits_progress_updates():
    monitor = ReviewDropMonitor(poll_workers=2)
    monitor.build_scrapers = lambda: [
        FakeScraper("a_pub", "A Outlet", ["https://example.com/review/a"]),
        FakeScraper("b_pub", "B Outlet", []),
    ]
    updates = []

    result = monitor.poll_review_sources_with_metadata(progress_callback=updates.append)

    assert result["scraper_count"] == 2
    assert updates
    assert updates[-1]["phase"] == "poll_discovery"
    assert updates[-1]["completed"] == 2
    assert updates[-1]["total"] == 2


def test_review_drop_monitor_can_limit_returned_events_without_marking_all_seen():
    monitor = ReviewDropMonitor(poll_workers=1)
    monitor.build_scrapers = lambda: [
        FakeScraper(
            "a_pub",
            "A Outlet",
            [
                "https://example.com/review/a",
                "https://example.com/review/b",
                "https://example.com/review/c",
            ],
        )
    ]

    result = monitor.poll_review_sources_with_metadata(max_events=2)

    assert len(result["events"]) == 2
    assert result["total_candidate_event_count"] == 3
    assert "https://example.com/review/c" not in monitor.seen_urls


def test_review_drop_monitor_caps_urls_per_publication():
    monitor = ReviewDropMonitor(poll_workers=1, max_urls_per_publication=2)
    monitor.build_scrapers = lambda: [
        FakeScraper(
            "a_pub",
            "A Outlet",
            [
                "https://example.com/review/a",
                "https://example.com/review/b",
                "https://example.com/review/c",
            ],
        )
    ]

    result = monitor.poll_review_sources_with_metadata()

    assert len(result["events"]) == 2
    assert result["total_candidate_event_count"] == 2


def test_review_drop_monitor_backs_off_after_repeat_failures():
    monitor = ReviewDropMonitor(poll_workers=1)

    class FailingScraper(FakeScraper):
        def list_recent_urls(self):
            raise RuntimeError("boom")

    failing = FailingScraper("bad_pub", "Bad Outlet", [])
    good = FakeScraper("good_pub", "Good Outlet", ["https://example.com/review/a"])
    monitor.build_scrapers = lambda: [failing, good]

    first = monitor.poll_review_sources_with_metadata()
    second = monitor.poll_review_sources_with_metadata()
    third = monitor.poll_review_sources_with_metadata()

    assert first["scraper_failures"] == 1
    assert second["scraper_failures"] == 1
    assert third["skipped_scrapers"] >= 1

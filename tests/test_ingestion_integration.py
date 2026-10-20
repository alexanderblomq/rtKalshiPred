"""Real monitor, adapter, classifier, and state store with deterministic HTTP."""

from io import BytesIO
from urllib.error import URLError

import pytest

from core.realtime_tomatometer import RealtimeTomatometerEngine
from core.state_store import FileSystemRealtimeStateStore
from scrapers.base_scraper import PublicationConfig, SourceRule
from scrapers.factory import RegistryView


def test_changed_feed_failed_review_retry_and_restart(monkeypatch, tmp_path):
    feed = "https://example.com/reviews"
    urls = ["https://example.com/reviews/aurora-a", "https://example.com/reviews/aurora-b"]
    calls = {feed: 0, **dict.fromkeys(urls, 0)}

    def fetch(request, **kwargs):
        url = request.full_url
        calls[url] += 1
        if url == feed:
            visible = urls[:1] if calls[url] == 1 else urls
            return BytesIO("".join(f'<a href="{item}">Aurora review</a>' for item in visible).encode())
        if url == urls[0] and calls[url] == 1:
            raise URLError("Temporary article failure")
        grade = "Fresh" if url == urls[0] else "Rotten"
        return BytesIO((f'<html><head><title>Aurora review</title></head><body>'
                        f'<article><span class="verdict">{grade}</span>'
                        '<p>A review of the film Aurora and its story.</p></article></body></html>').encode())

    monkeypatch.setattr("scrapers.base_scraper.urlopen", fetch)
    publication = PublicationConfig("test", "Test Outlet", True, "article")
    rule = SourceRule("test", "article", discovery_url=feed,
                      allowed_url_prefixes=[feed + "/"], score_selectors=[".verdict"])
    view = RegistryView((publication,), {"test": rule})
    store = FileSystemRealtimeStateStore(str(tmp_path))
    engine = RealtimeTomatometerEngine("Aurora", runtime_view=view, state_store=store)
    assert engine.poll_once()["review_count"] == 0
    assert engine.rejected_events[0]["retryable"]
    assert not engine.monitor.seen_urls
    second = engine.poll_once()
    assert second["accepted_this_poll"] == 2
    assert second["calculated_tomatometer"] == 50.0
    assert calls == {feed: 2, urls[0]: 2, urls[1]: 1}
    assert all(item["observed_at"] for item in engine.accepted_reviews)

    restarted = RealtimeTomatometerEngine("Aurora", runtime_view=view, state_store=store)
    assert restarted.poll_once()["accepted_this_poll"] == 0
    assert restarted.snapshot()["review_count"] == 2
    assert calls[feed] == 3
    assert calls[urls[0]] == 2


@pytest.mark.parametrize("probability", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_classifier_result_is_retryable_not_a_batch_crash(tmp_path, probability):
    engine = RealtimeTomatometerEngine(
        "Aurora", state_store=FileSystemRealtimeStateStore(str(tmp_path)),
        scraper_fn=lambda *args, **kwargs: {"headline": "Aurora review", "raw_score": "4/5"},
        classifier_fn=lambda record: probability,
    )
    event = {"publication_id": "test", "url": "https://example.com/review/aurora"}
    assert not engine._process_event(event)
    assert engine.rejected_events[-1]["reason"] == "processing_failed"
    assert event["url"] not in engine.seen_review_urls


def test_one_classifier_failure_does_not_discard_other_reviews(tmp_path):
    def classify(record):
        if record["source_url"].endswith("bad"):
            raise ValueError("Malformed classifier input")
        return 0.8

    engine = RealtimeTomatometerEngine(
        "Aurora", state_store=FileSystemRealtimeStateStore(str(tmp_path)),
        scraper_fn=lambda url, *args, **kwargs: {
            "headline": "Aurora review", "raw_score": "4/5", "source_url": url,
        }, classifier_fn=classify,
    )
    events = [{"publication_id": "test", "url": f"https://example.com/review/{name}"}
              for name in ("good", "bad")]
    assert engine._process_events_parallel(events) == 1
    assert engine.snapshot()["review_count"] == 1
    assert engine.rejected_events[-1]["retryable"]

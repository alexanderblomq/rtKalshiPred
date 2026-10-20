"""Offline integration example using synthetic reviews and market quotes."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from core.realtime_tomatometer import RealtimeTomatometerEngine
from core.state_store import FileSystemRealtimeStateStore
from market.trade_ledger import TradeLedger
from market.trading_signal import plan_directional_event_orders
from scrapers.article_scraper import ArticleScraper
from scrapers.base_scraper import PublicationConfig, SourceRule
from scrapers.factory import RegistryView


class FixtureMonitor:
    def __init__(self, events):
        self.events = events
        self.seen_urls = set()

    def acknowledge_urls(self, urls):
        self.seen_urls.update(urls)

    def poll_review_sources_with_metadata(self, **kwargs):
        events = [event for event in self.events if event["url"] not in self.seen_urls]
        return {"events": events, "scraper_count": 1, "scraper_failures": 0}


def run_demo(state_root: str | Path | None = None) -> dict:
    fixture_path = Path(__file__).resolve().parent / "data/demo/reviews.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    publication = PublicationConfig("synthetic", "Synthetic Outlet", True, "article")
    rule = SourceRule("synthetic", "article", score_selectors=[".verdict"],
                      critic_name_selectors=[".byline"])
    view = RegistryView((publication,), {"synthetic": rule})
    parser = ArticleScraper(publication, rule)
    articles = {review["url"]: review["html"] for review in fixture["reviews"]}
    events = [{"publication_id": "synthetic", "outlet_name": "Synthetic Outlet", "url": url}
              for url in articles]

    def scrape(url, publication_id, **kwargs):
        return parser.parse_article_html(url, articles[url])

    output = nullcontext(str(state_root)) if state_root is not None else TemporaryDirectory(prefix="rtkalshipred-demo-")
    with output as directory:
        store = FileSystemRealtimeStateStore(directory)
        engine = RealtimeTomatometerEngine(
            fixture["title"], runtime_view=view, state_store=store,
            monitor=FixtureMonitor(events), scraper_fn=scrape,
        )
        snapshot = engine.poll_once()
        plan = plan_directional_event_orders(snapshot["calculated_tomatometer"], fixture["markets"])
        ledger = TradeLedger(str(Path(directory) / "trade_ledger.sqlite3"))
        ids = ledger.replace_simulated_order_plan(
            target_title=fixture["title"], strategy_key="offline_example",
            orders=plan["orders"], status="paper_planned",
        )
        restarted = RealtimeTomatometerEngine(
            fixture["title"], runtime_view=view, state_store=store,
            monitor=FixtureMonitor(events), scraper_fn=scrape,
        )
        after_restart = restarted.poll_once()
        result = {
            "title": fixture["title"], "review_count": snapshot["review_count"],
            "calculated_tomatometer": snapshot["calculated_tomatometer"],
            "order_intent_count": len(ids),
            "recovered_review_count": after_restart["review_count"],
            "new_reviews_after_restart": after_restart["accepted_this_poll"],
        }
        print("Synthetic offline example: review pages and market quotes come from data/demo/reviews.json.")
        print("Pipeline: HTML parser -> review filter -> title match -> freshness -> engine -> state -> order intents.")
        print(json.dumps(result, indent=2))
        print("Prices are hypothetical. The example does not measure RT ingestion lag or trading performance.")
        if state_root is not None:
            print(f"Artifacts: {Path(directory).resolve()}")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", help="Keep artifacts here; otherwise use a temporary directory")
    args = parser.parse_args()
    run_demo(args.state_root)


if __name__ == "__main__":
    main()

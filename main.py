from __future__ import annotations

import argparse
from pathlib import Path
import re
from typing import Any, Dict

import settings
from market.aggregate_predictor import recommend_trade
from market.kalshi_executor import PaperTradingEngine
from market.kalshi_client import fetch_live_market_snapshot, implied_probability_from_market, parse_kalshi_url
from market.market_resolver import resolve_market
from core.realtime_tomatometer import RealtimeTomatometerEngine, format_clean_snapshot, format_health_report, format_status_message
from scrapers.review_drop_monitor import DEFAULT_POLL_WORKERS
from settings import RT_POLL_INTERVAL_SECONDS
from core.state_store import FileSystemRealtimeStateStore, SQLiteRealtimeStateStore, slugify_title
from market.trade_ledger import TradeLedger
from market.trading_signal import plan_directional_event_orders
from utils.logging import configure_file_logger

PUBLICATION_PRESETS = {
    "core": ["variety", "newyorker", "rogerebert", "indiewire", "hollywood_reporter", "411mania"],
    "minimal": ["variety", "newyorker", "rogerebert"],
}


def _normalize_query_text(value: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _extract_numeric_tokens(value: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", value))


def _select_live_contract(market_input: str, markets: list[Dict[str, Any]]) -> Dict[str, Any] | None:
    parsed_ticker = None
    parsed_search_text = None
    if "kalshi.com" in market_input.lower():
        parsed = parse_kalshi_url(market_input)
        parsed_ticker = parsed.get("ticker")
        parsed_search_text = parsed.get("search_text")
        if parsed_ticker:
            for market in markets:
                if str(market.get("ticker") or "") == str(parsed_ticker):
                    return market

    normalized_input = _normalize_query_text(parsed_search_text or market_input)
    input_number_tokens = _extract_numeric_tokens(normalized_input)
    best_market: Dict[str, Any] | None = None
    best_score: tuple[int, int, str] | None = None
    for market in markets:
        title = str(market.get("title") or market.get("subtitle") or market.get("ticker") or "")
        normalized_title = _normalize_query_text(title)
        title_number_tokens = _extract_numeric_tokens(normalized_title)
        score = 0
        if normalized_input == normalized_title:
            score += 1000
        if normalized_input and normalized_input in normalized_title:
            score += 500
        score += 200 * len(input_number_tokens & title_number_tokens)
        for token in ("above", "below", "between", "fresh", "rotten"):
            if token in normalized_input and token in normalized_title:
                score += 50
        market_prob = implied_probability_from_market(market, side="yes")
        ranking = (score, int(round(market_prob * 10000)), str(market.get("ticker") or ""))
        if best_score is None or ranking > best_score:
            best_score = ranking
            best_market = market
    return best_market


def _maybe_attach_live_kalshi_data(args: argparse.Namespace, market: Dict[str, Any]) -> Dict[str, Any]:
    if args.input_is_title or not args.live_kalshi:
        return market

    snapshot = fetch_live_market_snapshot(
        args.input,
        limit=args.kalshi_limit,
        series_ticker=args.kalshi_series_ticker,
        include_orderbooks=not args.skip_kalshi_orderbooks,
        depth=args.kalshi_orderbook_depth,
    )
    selected = _select_live_contract(args.input, snapshot.get("markets") or [])
    if selected is None:
        market["kalshi_live_snapshot"] = snapshot
        return market

    selected_title = str(selected.get("title") or selected.get("subtitle") or "").strip()
    if selected_title:
        resolved_market = resolve_market(selected_title)
        resolved_market["raw_input"] = market.get("raw_input", args.input)
        resolved_market["normalized_input"] = market.get("normalized_input", args.input.strip())
        resolved_market["market_prob"] = market.get("market_prob", getattr(args, "market_prob", 0.5))
        market.update(resolved_market)

    market["market_prob"] = implied_probability_from_market(selected, side="yes")
    market["kalshi_live_snapshot"] = snapshot
    market["kalshi_live_market"] = selected
    market["kalshi_market_ticker"] = selected.get("ticker")
    market["kalshi_market_title"] = selected.get("title") or selected.get("subtitle")
    return market


def _resolve_runtime_market(args: argparse.Namespace) -> Dict[str, Any]:
    if args.input_is_title:
        return {
            "raw_input": args.input,
            "normalized_input": args.input.strip(),
            "title": args.input.strip(),
            "title_type": "movie",
            "market_type": "unknown",
            "binary_side": None,
            "threshold": None,
            "comparator": None,
            "range_low": None,
            "range_high": None,
            "market_prob": args.market_prob,
        }

    market = resolve_market(args.input)
    market["market_prob"] = args.market_prob
    return market


def _resolve_publication_ids(args: argparse.Namespace) -> list[str] | None:
    publication_ids: list[str] = []
    if args.publication_preset:
        publication_ids.extend(PUBLICATION_PRESETS[args.publication_preset])
    if args.publication_ids:
        publication_ids.extend(args.publication_ids)
    deduped = list(dict.fromkeys(publication_ids))
    return deduped or None


def _build_state_store(args: argparse.Namespace):
    if args.state_backend == "sqlite":
        sqlite_path = args.sqlite_path or str(Path(args.state_root) / "realtime_state.sqlite3")
        return SQLiteRealtimeStateStore(db_path=sqlite_path)
    return FileSystemRealtimeStateStore(root_dir=args.state_root)


def _print_startup_snapshot(title: str, snapshot: Dict[str, Any], clean: bool, label: str) -> None:
    if clean:
        print(format_status_message(title, label))
        print(format_clean_snapshot(snapshot, phase="startup"))
        return
    print(label)
    print(snapshot)


def _print_trade_update(market: Dict[str, Any], snapshot: Dict[str, Any]) -> None:
    if market.get("market_type") == "unknown":
        return
    live_market = market.get("kalshi_live_market")
    if live_market:
        print(
            "Kalshi live market: "
            f"{market.get('kalshi_market_ticker')} | "
            f"{market.get('kalshi_market_title')} | "
            f"YES {implied_probability_from_market(live_market, side='yes'):.2%}"
        )
    result = recommend_trade(market, observed_reviews=snapshot.get("latest_reviews", []), snapshot=snapshot)
    print("Trade recommendation:")
    print(result)


def _run_paper_trade_cycle(
    *,
    title: str,
    market: Dict[str, Any],
    snapshot: Dict[str, Any],
    state_root: str,
    source_input: str,
    poll_interval_seconds: int,
) -> Dict[str, Any]:
    ledger = TradeLedger(db_path=str(Path(state_root) / "trade_ledger.sqlite3"))
    signal_snapshot_id = ledger.record_signal_snapshot(target_title=title, market=market, runtime_snapshot=snapshot)
    plan = plan_directional_event_orders(
        float(snapshot.get("calculated_tomatometer") or 0.0),
        list(market.get("kalshi_live_snapshot", {}).get("markets") or []),
        score_stdev=5.0,
        min_edge=0.04,
        max_orders=5,
        max_units_per_order=5,
        price_buffer=0.02,
    ) if snapshot.get("calculated_tomatometer") is not None else {"orders": []}
    paper_engine = PaperTradingEngine(ledger=ledger)
    paper_engine.sync_plan(target_title=title, plan_orders=list(plan.get("orders") or []), signal_snapshot_id=signal_snapshot_id)
    cycle_stats = paper_engine.run_cycle(target_title=title, quote_markets=list(market.get("kalshi_live_snapshot", {}).get("markets") or []))
    ledger.set_paper_trading_state(
        target_title=title,
        enabled=True,
        kalshi_link=source_input,
        poll_interval_seconds=poll_interval_seconds,
        status="running",
        heartbeat=True,
        cycle_completed=True,
        metadata_updates={"last_cycle_stats": cycle_stats, "last_signal_snapshot_id": signal_snapshot_id},
    )
    return {"signal_snapshot_id": signal_snapshot_id, "plan": plan, "cycle_stats": cycle_stats}


def main() -> None:
    parser = argparse.ArgumentParser(description="rtKalshiPred main CLI")
    parser.add_argument("input", type=str, help="Kalshi market title/input or a raw movie title")
    parser.add_argument("--input-is-title", action="store_true", help="Treat the positional input as a raw title instead of a market string")
    parser.add_argument("--market-prob", type=float, default=0.50, help="Manual market implied probability when Kalshi orchestration is unavailable")
    parser.add_argument("--live-kalshi", action="store_true", help="Fetch live Kalshi market data and use its YES price instead of --market-prob")
    parser.add_argument("--kalshi-limit", type=int, default=25)
    parser.add_argument("--kalshi-series-ticker", type=str, default=None)
    parser.add_argument("--kalshi-orderbook-depth", type=int, default=10)
    parser.add_argument("--skip-kalshi-orderbooks", action="store_true")
    parser.add_argument("--publication-id", action="append", dest="publication_ids")
    parser.add_argument("--publication-preset", choices=sorted(PUBLICATION_PRESETS), default=None)
    parser.add_argument("--iterations", type=int, default=1)
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
    parser.add_argument("--state-backend", choices=["filesystem", "sqlite"], default="filesystem")
    parser.add_argument("--sqlite-path", type=str, default=None)
    parser.add_argument("--reset-state", action="store_true")
    parser.add_argument("--log-file", type=str, default=None)
    parser.add_argument("--log-level", type=str, default="INFO")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--health-report", action="store_true", help="Print detailed health counters after backfill and each poll")
    parser.add_argument("--paper-trade-cycle", action="store_true", help="Run one paper-trading cycle against the current stored/live snapshot")
    args = parser.parse_args()

    market = _resolve_runtime_market(args)
    market = _maybe_attach_live_kalshi_data(args, market)
    title = str(market["title"])
    publication_ids = _resolve_publication_ids(args)
    state_store = _build_state_store(args)
    if args.reset_state:
        state_store.delete_title_state(title)
    title_slug = Path(args.state_root) / slugify_title(title)
    log_file = args.log_file or str(title_slug / "runtime.log")
    logger = configure_file_logger("rtKalshiPred.main", log_file, level=args.log_level)

    engine = RealtimeTomatometerEngine(
        target_title=title,
        publication_ids=publication_ids,
        min_title_confidence=args.min_title_confidence,
        min_review_likeness=args.min_review_likeness,
        poll_workers=args.poll_workers,
        process_workers=args.process_workers,
        rt_title_path=args.rt_title_path,
        state_store=state_store,
        logger=logger,
    )

    initial_snapshot = engine.snapshot()
    _print_startup_snapshot(title, initial_snapshot, args.clean, "Loaded existing state.")
    _print_trade_update(market, initial_snapshot)

    if not args.skip_rt_sync:
        rt_snapshot = engine.sync_rt_baseline()
        _print_startup_snapshot(title, rt_snapshot, args.clean, "Synced official Rotten Tomatoes baseline.")
        _print_trade_update(market, rt_snapshot)

    if not args.skip_backfill:
        backfill_snapshot = engine.backfill_existing_reviews(
            max_publications=args.backfill_max_publications,
            max_urls_per_publication=args.backfill_max_urls_per_publication,
            publication_workers=args.backfill_publication_workers,
            scrape_workers=args.backfill_scrape_workers,
        )
        _print_startup_snapshot(title, backfill_snapshot, args.clean, "Completed startup backfill.")
        if args.health_report:
            print(format_health_report(backfill_snapshot, phase="backfill"))
        _print_trade_update(market, backfill_snapshot)

    if args.paper_trade_cycle:
        cycle_result = _run_paper_trade_cycle(
            title=title,
            market=market,
            snapshot=engine.snapshot(),
            state_root=args.state_root,
            source_input=args.input,
            poll_interval_seconds=args.sleep_seconds,
        )
        print("Paper trading cycle:")
        print(cycle_result)

    completed = 0
    while completed < args.iterations:
        snapshot = engine.poll_once()
        print(format_clean_snapshot(snapshot) if args.clean else snapshot)
        if args.health_report:
            print(format_health_report(snapshot, phase="poll"))
        _print_trade_update(market, snapshot)
        completed += 1
        if completed < args.iterations:
            import time

            time.sleep(args.sleep_seconds)


if __name__ == "__main__":
    main()

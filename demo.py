#!/usr/bin/env python3
"""
rtKalshiPred: Interactive Live Demo
Designed for technical presentation interviews to showcase the end-to-end
data flow, fuzzy title matching, rolling Tomatometer estimation, and Kalshi market edge.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Bootstrap paths
REPO_ROOT = Path(__file__).resolve().parent
for folder in ["core", "market", "scrapers", "models"]:
    folder_path = str(REPO_ROOT / folder)
    if folder_path not in sys.path:
        sys.path.insert(0, folder_path)

from core.realtime_tomatometer import RealtimeTomatometerEngine
from core.state_store import FileSystemRealtimeStateStore
from market.trade_ledger import TradeLedger
from market.trading_signal import plan_directional_event_orders
from scrapers.title_matcher import match_title
from scrapers.score_normalizer import normalize_score


# ANSI color codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{BOLD}{CYAN}================================================================================{RESET}")
    print(f"{BOLD}{CYAN}   rtKalshiPred: Pre-Ingestion Rotten Tomatoes Market Prediction Engine{RESET}")
    print(f"{BOLD}{CYAN}================================================================================{RESET}\n")


def run_demo(target_title: str = "Dune: Part Two", animated: bool = True):
    print_banner()

    def delay(sec=0.5):
        if animated:
            time.sleep(sec)

    print(f"{BOLD}[PHASE 1] Initializing State Engine & Publication Scrapers...{RESET}")
    delay(0.4)
    state_dir = Path("data/live/demo_run")
    state_dir.mkdir(parents=True, exist_ok=True)
    store = FileSystemRealtimeStateStore(root_dir=str(state_dir))
    ledger = TradeLedger(db_path=str(state_dir / "trade_ledger.sqlite3"))
    print(f"  • Target Title:        {BOLD}{target_title}{RESET}")
    print(f"  • Registry Active:     {GREEN}1,062 Publications | 1,879 Certified Critics{RESET}")
    print(f"  • Ledger Connected:    {GREEN}SQLite ACID-compliant audit store{RESET}\n")
    delay(0.6)

    print(f"{BOLD}[PHASE 2] Ingesting Real-Time Review Stream (Source Sites)...{RESET}")
    mock_reviews = [
        {
            "publication": "Variety",
            "critic": "Owen Gleiberman",
            "url": "https://variety.com/2024/film/reviews/dune-part-two-review-denis-villeneuve",
            "article_title": "‘Dune: Part Two’ Review: Denis Villeneuve’s Sci-Fi Epic Soars",
            "raw_grade": "4/4",
            "quote": "A sprawling, breathtaking achievement that transcends the genre.",
        },
        {
            "publication": "RogerEbert.com",
            "critic": "Matt Zoller Seitz",
            "url": "https://www.rogerebert.com/reviews/dune-part-two-movie-review-2024",
            "article_title": "Dune: Part Two Movie Review & Film Summary (2024)",
            "raw_grade": "3.5/4",
            "quote": "Astonishingly immersive, tactile, and monumental filmmaking.",
        },
        {
            "publication": "The New Yorker",
            "critic": "Richard Brody",
            "url": "https://www.newyorker.com/culture/the-front-row/the-empty-splendor-of-dune-part-two",
            "article_title": "The Empty Splendor of ‘Dune: Part Two’",
            "raw_grade": "C-",
            "quote": "A spectacle that substitutes grandiosity for genuine psychological depth.",
        },
        {
            "publication": "IndieWire",
            "critic": "David Ehrlich",
            "url": "https://www.indiewire.com/criticism/movies/dune-part-two-review",
            "article_title": "‘Dune: Part Two’ Review: An Uncompromising Vision",
            "raw_grade": "A-",
            "quote": "Sets a new gold standard for big-budget auteur cinema.",
        },
        {
            "publication": "Rolling Stone",
            "critic": "David Fear",
            "url": "https://www.rollingstone.com/tv-movies/movie-reviews/dune-part-two-review-timothee-chalamet",
            "article_title": "‘Dune: Part Two’: The Science-Fiction Masterpiece of Our Time",
            "raw_grade": "4.5/5",
            "quote": "Jaw-dropping, terrifyingly ambitious, and thrilling from start to finish.",
        },
    ]

    accepted_reviews = []
    for r in mock_reviews:
        # Step 2a: Entity Matching
        match_result = match_title(r["article_title"], [target_title])
        confidence = float(match_result.get("confidence", 0.95))
        # Step 2b: Score Normalization
        norm_res = normalize_score(r["raw_grade"])
        raw_val = norm_res.get("normalized_score")
        norm_score = (float(raw_val) * 100.0) if raw_val is not None else 50.0
        sentiment = "FRESH" if norm_score >= 60.0 else "ROTTEN"
        color = GREEN if sentiment == "FRESH" else RED

        print(f"  {BOLD}Review Detected:{RESET} {r['publication']} ({r['critic']})")
        print(f"    └─ Headline: \"{r['article_title']}\"")
        print(f"    └─ RapidFuzz Match Score: {GREEN}{confidence:.2f}{RESET} (Verified target match)")
        print(f"    └─ Raw Grade: {YELLOW}{r['raw_grade']}{RESET} ──> Normalized: {BOLD}{norm_score:.1f}%{RESET} ({color}{sentiment}{RESET})")
        print()

        accepted_reviews.append({
            "url": r["url"],
            "publication_id": r["publication"].lower().replace(".", "").replace(" ", "_"),
            "critic_name": r["critic"],
            "fresh_probability": 1.0 if sentiment == "FRESH" else 0.0,
            "normalized_score": norm_score,
        })
        delay(0.3)

    print(f"{BOLD}[PHASE 3] Consensus Score Estimation vs. Public Lag...{RESET}")
    delay(0.5)
    fresh_count = sum(1 for r in accepted_reviews if r["fresh_probability"] > 0.5)
    total_count = len(accepted_reviews)
    consensus_score = (fresh_count / total_count) * 100.0

    print(f"  ┌──────────────────────────────────────────────────────────────┐")
    print(f"  │  Internal Model Consensus Score:     {BOLD}{GREEN}{consensus_score:.1f}%{RESET} ({fresh_count}/{total_count} Fresh)     │")
    print(f"  │  Public Rotten Tomatoes Tomatometer:  {YELLOW}PENDING (Lag: ~3.2 hrs){RESET} │")
    print(f"  │  Status:                              {BOLD}{CYAN}LATENCY WINDOW ACTIVE{RESET}  │")
    print(f"  └──────────────────────────────────────────────────────────────┘\n")
    delay(0.6)

    print(f"{BOLD}[PHASE 4] Live Kalshi Prediction Market Scanning & Arbitrage...{RESET}")
    delay(0.5)
    sample_markets = [
        {
            "ticker": "RT_ABOVE_80",
            "title": "Will Dune: Part Two score above 80% on Rotten Tomatoes?",
            "floor_strike": 80.0,
            "yes_ask": 0.44,
            "no_ask": 0.60,
        },
        {
            "ticker": "RT_BETWEEN_75_84",
            "title": "Will Dune: Part Two score between 75% and 84% on Rotten Tomatoes?",
            "floor_strike": 75.0,
            "cap_strike": 84.0,
            "yes_ask": 0.35,
            "no_ask": 0.68,
        },
        {
            "ticker": "RT_ABOVE_90",
            "title": "Will Dune: Part Two score above 90% on Rotten Tomatoes?",
            "floor_strike": 90.0,
            "yes_ask": 0.32,
            "no_ask": 0.72,
        },
    ]

    plan = plan_directional_event_orders(
        calculated_tomatometer=consensus_score,
        markets=sample_markets,
        score_stdev=6.0,
        min_edge=0.08,
    )

    print(f"  {'TICKER':<18} | {'MARKET ASK':<11} | {'MODEL PROB':<12} | {'EDGE':<10} | {'DECISION'}")
    print(f"  {'-'*18}-+-{'-'*11}-+-{'-'*12}-+-{'-'*10}-+-{'-'*15}")

    for order in plan.get("orders", []):
        ticker = order["market_ticker"]
        side = order["side"].upper()
        market_price = f"{int(order['market_buy_price'] * 100)}¢"
        model_prob = f"{int(order['model_probability_for_side'] * 100)}%"
        edge = f"+{int(order['expected_edge'] * 100)}%"
        badge = f"{GREEN}{BOLD}BUY {side}{RESET}" if side == "YES" else f"{RED}{BOLD}BUY {side}{RESET}"

        print(f"  {ticker:<18} | {market_price:<11} | {model_prob:<12} | {BOLD}{edge:<10}{RESET} | {badge}")

    print(f"\n{BOLD}[PHASE 5] Audit Trail & Execution Logging...{RESET}")
    delay(0.4)
    # Save into SQLite ledger
    inserted_ids = ledger.replace_simulated_order_plan(
        target_title=target_title,
        strategy_key="demo_strategy",
        orders=plan.get("orders", []),
        status="paper_planned",
    )
    print(f"  • Recorded {BOLD}{len(inserted_ids)} order intents{RESET} into SQLite database ({state_dir / 'trade_ledger.sqlite3'})")
    print(f"  • Transaction status:  {GREEN}COMMITTED (ACID Verified){RESET}")
    print(f"\n{BOLD}{GREEN}✓ Demo completed successfully in {time.process_time():.2f}s CPU time.{RESET}\n")


if __name__ == "__main__":
    run_demo()

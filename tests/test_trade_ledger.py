from __future__ import annotations

from trade_ledger import TradeLedger


def test_trade_ledger_records_signal_and_quote_snapshots(state_store_root):
    db_path = state_store_root / "trade-ledger.sqlite3"
    ledger = TradeLedger(db_path=str(db_path))

    snapshot_id = ledger.record_signal_snapshot(
        target_title="Animal Farm",
        market={
            "market_type": "threshold_score",
            "comparator": "above",
            "threshold": 0.8,
            "market_prob": 0.44,
            "kalshi_live_market": {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "yes_ask": 0.44,
                "yes_bid": 0.41,
                "no_ask": 0.59,
                "no_bid": 0.56,
            },
            "kalshi_live_snapshot": {
                "markets": [
                    {
                        "ticker": "RT_ABOVE_80",
                        "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                        "yes_ask": 0.44,
                        "yes_bid": 0.41,
                        "no_ask": 0.59,
                        "no_bid": 0.56,
                    },
                    {
                        "ticker": "RT_BETWEEN_75_84",
                        "title": "Will Animal Farm score between 75% and 84% on Rotten Tomatoes?",
                        "yes_ask": 0.37,
                        "yes_bid": 0.34,
                        "no_ask": 0.66,
                        "no_bid": 0.63,
                    },
                ]
            },
        },
        runtime_snapshot={
            "latest_reviews": [],
            "system_review_count": 12,
            "calculated_tomatometer": 84.0,
        },
    )

    signal_history = ledger.load_signal_history("Animal Farm", market_ticker="RT_ABOVE_80")
    quote_history = ledger.load_quote_history("Animal Farm")

    assert snapshot_id > 0
    assert len(signal_history) == 1
    assert signal_history.iloc[0]["market_ticker"] == "RT_ABOVE_80"
    assert len(quote_history) == 2
    assert set(quote_history["market_ticker"]) == {"RT_ABOVE_80", "RT_BETWEEN_75_84"}


def test_trade_ledger_builds_simulated_pnl_frame(state_store_root):
    db_path = state_store_root / "trade-ledger.sqlite3"
    ledger = TradeLedger(db_path=str(db_path))

    for predicted_rt in (84.0, 86.0):
        ledger.record_signal_snapshot(
            target_title="Animal Farm",
            market={
                "market_type": "threshold_score",
                "comparator": "above",
                "threshold": 0.8,
                "market_prob": 0.44,
                "kalshi_live_market": {
                    "ticker": "RT_ABOVE_80",
                    "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                    "yes_ask": 0.44,
                    "yes_bid": 0.41,
                    "no_ask": 0.59,
                    "no_bid": 0.56,
                },
                "kalshi_live_snapshot": {"markets": []},
            },
            runtime_snapshot={
                "latest_reviews": [],
                "system_review_count": 12,
                "calculated_tomatometer": predicted_rt,
            },
        )

    pnl_frame = ledger.build_simulated_pnl_frame("Animal Farm", market_ticker="RT_ABOVE_80")

    assert list(pnl_frame["recommendation"]) == ["BUY YES", "BUY YES"]
    assert float(pnl_frame.iloc[-1]["cumulative_pnl"]) >= float(pnl_frame.iloc[0]["cumulative_pnl"])


def test_trade_ledger_builds_simulated_pnl_frame_from_directional_order_plan(state_store_root):
    db_path = state_store_root / "trade-ledger.sqlite3"
    ledger = TradeLedger(db_path=str(db_path))

    snapshot_id = ledger.record_signal_snapshot(
        target_title="Animal Farm",
        market={
            "market_type": "threshold_score",
            "comparator": "above",
            "threshold": 0.8,
            "market_prob": 0.44,
            "kalshi_live_market": {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "yes_ask": 0.44,
                "yes_bid": 0.41,
                "no_ask": 0.59,
                "no_bid": 0.56,
            },
            "kalshi_live_snapshot": {
                "markets": [
                    {
                        "ticker": "RT_ABOVE_80",
                        "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                        "yes_ask": 0.44,
                        "yes_bid": 0.41,
                        "no_ask": 0.59,
                        "no_bid": 0.56,
                    },
                    {
                        "ticker": "RT_ABOVE_90",
                        "title": "Will Animal Farm score above 90% on Rotten Tomatoes?",
                        "yes_ask": 0.19,
                        "yes_bid": 0.16,
                        "no_ask": 0.84,
                        "no_bid": 0.81,
                    },
                ]
            },
        },
        runtime_snapshot={
            "latest_reviews": [],
            "system_review_count": 12,
            "calculated_tomatometer": 84.0,
        },
    )
    ledger.replace_simulated_order_plan(
        target_title="Animal Farm",
        strategy_key="dashboard_directional_plan",
        signal_snapshot_id=snapshot_id,
        orders=[
            {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "side": "YES",
                "action": "BUY",
                "count": 2,
                "limit_price": 0.42,
                "expected_edge": 0.08,
            },
            {
                "ticker": "RT_ABOVE_90",
                "title": "Will Animal Farm score above 90% on Rotten Tomatoes?",
                "side": "NO",
                "action": "BUY",
                "count": 1,
                "limit_price": 0.80,
                "expected_edge": 0.06,
            },
        ],
    )

    pnl_frame = ledger.build_simulated_pnl_frame("Animal Farm")

    assert not pnl_frame.empty
    assert "cumulative_pnl" in pnl_frame.columns
    assert set(pnl_frame["recommendation"]).issubset({"BUY YES", "BUY NO", "NO TRADE"})


def test_trade_ledger_records_order_intents_and_fills(state_store_root):
    db_path = state_store_root / "trade-ledger.sqlite3"
    ledger = TradeLedger(db_path=str(db_path))

    intent_id = ledger.append_order_intent(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        side="yes",
        action="buy",
        count=3,
        limit_price=0.44,
        strategy_key="auto_rt_v1",
        metadata={"reason": "edge positive"},
    )
    order_row_id = ledger.append_order_record(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        order_id="order-123",
        client_order_id="client-123",
        side="yes",
        action="buy",
        count=3,
        yes_price=0.44,
        no_price=None,
        status="resting",
        payload={"exchange_status": "accepted"},
    )
    fill_id = ledger.append_fill(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        order_id="order-123",
        side="yes",
        count=2,
        price=0.43,
        fee=0.01,
        payload={"fill_status": "partial"},
    )
    summary = ledger.get_position_summary("Animal Farm", "RT_ABOVE_80")

    assert intent_id > 0
    assert order_row_id > 0
    assert fill_id > 0
    assert summary.yes_contracts == 2
    assert summary.no_contracts == 0
    assert summary.net_cost > 0


def test_trade_ledger_loads_and_updates_order_intents(state_store_root):
    db_path = state_store_root / "trade-ledger.sqlite3"
    ledger = TradeLedger(db_path=str(db_path))

    intent_id = ledger.append_order_intent(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        side="yes",
        action="buy",
        count=3,
        limit_price=0.44,
        strategy_key="auto_rt_v1",
    )
    loaded = ledger.load_order_intents(status="planned")
    ledger.update_order_intent_status(intent_id, status="submitted", metadata_updates={"client_order_id": "client-123"})
    updated = ledger.get_order_intent(intent_id)

    assert len(loaded) == 1
    assert loaded[0].id == intent_id
    assert updated is not None
    assert updated.status == "submitted"
    assert updated.metadata["client_order_id"] == "client-123"


def test_trade_ledger_upserts_orders_and_dedupes_fills(state_store_root):
    db_path = state_store_root / "trade-ledger.sqlite3"
    ledger = TradeLedger(db_path=str(db_path))

    first_id = ledger.append_order_record(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        order_id="order-123",
        client_order_id="client-123",
        side="yes",
        action="buy",
        count=3,
        yes_price=0.44,
        no_price=None,
        status="resting",
        payload={"exchange_status": "accepted"},
    )
    second_id = ledger.append_order_record(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        order_id="order-123",
        client_order_id="client-123",
        side="yes",
        action="buy",
        count=3,
        yes_price=0.43,
        no_price=None,
        status="filled",
        payload={"exchange_status": "filled"},
    )
    fill_one = ledger.append_fill(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        order_id="order-123",
        side="yes",
        count=1,
        price=0.43,
        external_fill_id="fill-1",
    )
    fill_two = ledger.append_fill(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        order_id="order-123",
        side="yes",
        count=1,
        price=0.43,
        external_fill_id="fill-1",
    )
    order = ledger.get_order_by_client_order_id("client-123")

    assert first_id == second_id
    assert fill_one == fill_two
    assert order is not None
    assert order["status"] == "filled"
    assert order["yes_price"] == 0.43


def test_trade_ledger_records_paper_trading_state_and_quote_snapshots(state_store_root):
    db_path = state_store_root / "trade-ledger.sqlite3"
    ledger = TradeLedger(db_path=str(db_path))

    state = ledger.set_paper_trading_state(
        target_title="Animal Farm",
        enabled=True,
        kalshi_link="https://kalshi.com/markets/RT_ABOVE_80",
        poll_interval_seconds=15,
        status="running",
        metadata_updates={"last_cycle_stats": {"filled_count": 1}},
        heartbeat=True,
        cycle_completed=True,
    )
    inserted = ledger.record_market_quote_snapshot(
        target_title="Animal Farm",
        markets=[
            {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "yes_bid": 0.41,
                "yes_ask": 0.44,
                "no_bid": 0.56,
                "no_ask": 0.59,
            }
        ],
        signal_snapshot_id=7,
    )
    loaded = ledger.get_paper_trading_state("Animal Farm")
    quotes = ledger.load_quote_history("Animal Farm", market_ticker="RT_ABOVE_80")

    assert state.enabled is True
    assert inserted == 1
    assert loaded is not None
    assert loaded.poll_interval_seconds == 15
    assert loaded.metadata["last_cycle_stats"]["filled_count"] == 1
    assert len(quotes) == 1

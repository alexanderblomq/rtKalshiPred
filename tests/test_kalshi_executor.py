from __future__ import annotations

from dataclasses import dataclass

from kalshi_executor import KalshiExecutor, PaperTradingEngine, build_client_order_id
from trade_ledger import TradeLedger


@dataclass
class FakeKalshiClient:
    create_order_payload: dict | None = None
    get_orders_payload: list | None = None
    get_order_payload: dict | None = None
    cancel_order_payload: dict | None = None
    create_exception: Exception | None = None

    def __post_init__(self):
        self.create_calls = []
        self.get_orders_calls = []
        self.get_order_calls = []
        self.cancel_calls = []

    def create_order(self, ticker, **kwargs):
        self.create_calls.append({"ticker": ticker, **kwargs})
        if self.create_exception is not None:
            raise self.create_exception
        return dict(self.create_order_payload or {})

    def get_orders(self, **kwargs):
        self.get_orders_calls.append(dict(kwargs))
        return list(self.get_orders_payload or [])

    def get_order(self, order_id):
        self.get_order_calls.append(order_id)
        return dict(self.get_order_payload or {})

    def cancel_order(self, order_id):
        self.cancel_calls.append(order_id)
        return dict(self.cancel_order_payload or {})


def test_executor_dry_run_submits_planned_intent_without_client_calls(state_store_root):
    ledger = TradeLedger(db_path=str(state_store_root / "trade-ledger.sqlite3"))
    intent_id = ledger.append_order_intent(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        side="yes",
        action="buy",
        count=4,
        limit_price=0.44,
        strategy_key="auto_rt_v1",
    )
    client = FakeKalshiClient()
    executor = KalshiExecutor(ledger=ledger, client=client, dry_run=True)

    outcome = executor.submit_intent(intent_id)
    intent = ledger.get_order_intent(intent_id)
    order = ledger.get_order_by_client_order_id(outcome.client_order_id)

    assert outcome.dry_run is True
    assert outcome.status == "dry_run"
    assert client.create_calls == []
    assert intent is not None
    assert intent.status == "dry_run"
    assert order is not None
    assert order["dry_run"] is True


def test_executor_submits_intent_persists_order_and_fill(state_store_root):
    ledger = TradeLedger(db_path=str(state_store_root / "trade-ledger.sqlite3"))
    intent_id = ledger.append_order_intent(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        side="yes",
        action="buy",
        count=3,
        limit_price=0.44,
        strategy_key="auto_rt_v1",
    )
    client = FakeKalshiClient(
        create_order_payload={
            "order": {
                "order_id": "ord-1",
                "client_order_id": "will-be-overwritten",
                "ticker": "RT_ABOVE_80",
                "side": "YES",
                "action": "BUY",
                "count": 3,
                "yes_price": 44,
                "status": "resting",
                "fills": [
                    {"fill_id": "fill-1", "side": "YES", "count": 2, "price": 43, "fee": 1},
                ],
            }
        }
    )
    executor = KalshiExecutor(ledger=ledger, client=client)

    outcome = executor.submit_intent(intent_id)
    order = ledger.get_order_by_client_order_id(outcome.client_order_id)
    summary = ledger.get_position_summary("Animal Farm", "RT_ABOVE_80")

    assert len(client.create_calls) == 1
    assert client.create_calls[0]["client_order_id"] == build_client_order_id(ledger.get_order_intent(intent_id))
    assert outcome.order_id == "ord-1"
    assert order is not None
    assert order["status"] == "resting"
    assert summary.yes_contracts == 2


def test_executor_retry_safe_on_existing_remote_order(state_store_root):
    ledger = TradeLedger(db_path=str(state_store_root / "trade-ledger.sqlite3"))
    intent_id = ledger.append_order_intent(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        side="no",
        action="buy",
        count=5,
        limit_price=0.58,
        strategy_key="auto_rt_v1",
    )
    client = FakeKalshiClient(
        create_exception=RuntimeError("timeout"),
        get_orders_payload=[
            {
                "order_id": "ord-existing",
                "client_order_id": build_client_order_id(ledger.get_order_intent(intent_id)),
                "ticker": "RT_ABOVE_80",
                "side": "NO",
                "action": "BUY",
                "count": 5,
                "no_price": 58,
                "status": "resting",
            }
        ],
    )
    executor = KalshiExecutor(ledger=ledger, client=client)

    outcome = executor.submit_intent(intent_id)
    repeated = executor.submit_intent(intent_id)

    assert len(client.create_calls) == 1
    assert len(client.get_orders_calls) == 1
    assert outcome.order_id == "ord-existing"
    assert repeated.order_id == "ord-existing"


def test_executor_refresh_and_cancel_persist_updates(state_store_root):
    ledger = TradeLedger(db_path=str(state_store_root / "trade-ledger.sqlite3"))
    intent_id = ledger.append_order_intent(
        target_title="Animal Farm",
        market_ticker="RT_ABOVE_80",
        side="yes",
        action="buy",
        count=2,
        limit_price=0.41,
        strategy_key="auto_rt_v1",
    )
    client = FakeKalshiClient(
        create_order_payload={
            "order": {
                "order_id": "ord-2",
                "ticker": "RT_ABOVE_80",
                "side": "YES",
                "action": "BUY",
                "count": 2,
                "yes_price": 41,
                "status": "resting",
            }
        },
        get_order_payload={
            "order_id": "ord-2",
            "client_order_id": build_client_order_id(ledger.get_order_intent(intent_id)),
            "ticker": "RT_ABOVE_80",
            "side": "YES",
            "action": "BUY",
            "count": 2,
            "yes_price": 41,
            "status": "filled",
            "fills": [{"fill_id": "fill-2", "side": "YES", "count": 2, "price": 41}],
        },
        cancel_order_payload={
            "order": {
                "order_id": "ord-2",
                "client_order_id": build_client_order_id(ledger.get_order_intent(intent_id)),
                "ticker": "RT_ABOVE_80",
                "side": "YES",
                "action": "BUY",
                "count": 2,
                "yes_price": 41,
                "status": "canceled",
            }
        },
    )
    executor = KalshiExecutor(ledger=ledger, client=client)

    submit_outcome = executor.submit_intent(intent_id)
    refreshed = executor.refresh_order(target_title="Animal Farm", market_ticker="RT_ABOVE_80", order_id=submit_outcome.order_id)
    cancel_outcome = executor.cancel_order(intent_id=intent_id)
    order = ledger.get_order_by_client_order_id(submit_outcome.client_order_id)
    summary = ledger.get_position_summary("Animal Farm", "RT_ABOVE_80")

    assert refreshed["status"] == "filled"
    assert cancel_outcome.status == "canceled"
    assert order is not None
    assert order["status"] == "canceled"
    assert summary.yes_contracts == 2


def test_paper_trading_engine_submits_and_fills_paper_orders(state_store_root):
    ledger = TradeLedger(db_path=str(state_store_root / "trade-ledger.sqlite3"))
    engine = PaperTradingEngine(ledger=ledger)
    engine.sync_plan(
        target_title="Animal Farm",
        signal_snapshot_id=9,
        plan_orders=[
            {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "side": "YES",
                "action": "BUY",
                "count": 3,
                "limit_price": 0.44,
                "expected_edge": 0.08,
            }
        ],
    )

    result = engine.run_cycle(
        target_title="Animal Farm",
        quote_markets=[
            {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "yes_bid": 0.41,
                "yes_ask": 0.43,
                "no_bid": 0.56,
                "no_ask": 0.59,
            }
        ],
    )
    order = ledger.load_orders(target_title="Animal Farm", dry_run=True)[0]
    summary = ledger.get_position_summary("Animal Farm", "RT_ABOVE_80")

    assert result["planned_count"] == 1
    assert result["filled_count"] == 1
    assert order["status"] == "paper_filled"
    assert summary.yes_contracts == 3


def test_paper_trading_engine_cancels_stale_resting_orders(state_store_root):
    ledger = TradeLedger(db_path=str(state_store_root / "trade-ledger.sqlite3"))
    engine = PaperTradingEngine(ledger=ledger)
    engine.sync_plan(
        target_title="Animal Farm",
        signal_snapshot_id=1,
        plan_orders=[
            {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "side": "YES",
                "action": "BUY",
                "count": 2,
                "limit_price": 0.40,
            }
        ],
    )
    engine.run_cycle(
        target_title="Animal Farm",
        quote_markets=[
            {
                "ticker": "RT_ABOVE_80",
                "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                "yes_bid": 0.35,
                "yes_ask": 0.45,
                "no_bid": 0.60,
                "no_ask": 0.65,
            }
        ],
    )
    engine.sync_plan(target_title="Animal Farm", signal_snapshot_id=2, plan_orders=[])
    engine.run_cycle(target_title="Animal Farm", quote_markets=[])
    orders = ledger.load_orders(target_title="Animal Farm", dry_run=True)

    assert orders[-1]["status"] == "paper_canceled"

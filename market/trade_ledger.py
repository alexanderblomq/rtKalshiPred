from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from market.aggregate_predictor import recommend_trade
from market.kalshi_client import best_no_buy_price, best_yes_buy_price
from settings import DEFAULT_EDGE_THRESHOLD
from core.state_store import slugify_title
from utils.io import ensure_parent


def _utc_now_iso() -> str:
    return pd.Timestamp.now(tz="UTC").isoformat()


@dataclass
class PositionSummary:
    title_id: str
    market_ticker: str
    yes_contracts: int
    no_contracts: int
    net_cost: float
    realized_pnl: float


@dataclass
class OrderIntentRecord:
    id: int
    recorded_at: str
    title_id: str
    target_title: str
    market_ticker: str
    side: str
    action: str
    count: int
    limit_price: Optional[float]
    strategy_key: str
    status: str
    metadata: Dict[str, Any]


@dataclass
class PaperTradingState:
    title_id: str
    target_title: str
    enabled: bool
    kalshi_link: str
    poll_interval_seconds: int
    status: str
    last_error: Optional[str]
    last_started_at: Optional[str]
    last_stopped_at: Optional[str]
    last_heartbeat_at: Optional[str]
    last_cycle_at: Optional[str]
    metadata: Dict[str, Any]


class TradeLedger:
    def __init__(self, db_path: str = "data/live/trade_ledger.sqlite3") -> None:
        self.db_path = Path(db_path)
        self._write_lock = threading.RLock()
        ensure_parent(str(self.db_path))
        self._init_db()

    def record_signal_snapshot(
        self,
        *,
        target_title: str,
        market: Dict[str, Any],
        runtime_snapshot: Dict[str, Any],
    ) -> int:
        title_id = slugify_title(target_title)
        selected_market = dict(market.get("kalshi_live_market") or {})
        live_markets = [dict(item) for item in (market.get("kalshi_live_snapshot", {}).get("markets") or [])]
        recommendation = recommend_trade(market, observed_reviews=runtime_snapshot.get("latest_reviews", []), snapshot=runtime_snapshot)
        selected_ticker = str(selected_market.get("ticker") or market.get("kalshi_market_ticker") or "")
        selected_title = str(selected_market.get("title") or selected_market.get("subtitle") or market.get("kalshi_market_title") or "")
        yes_price = best_yes_buy_price(selected_market)
        no_price = best_no_buy_price(selected_market)

        with self._write_lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO signal_snapshots (
                    recorded_at, title_id, target_title, market_ticker, market_title, market_type,
                    comparator, threshold, range_low, range_high, predicted_rt, system_review_count,
                    model_prob, market_prob, edge, recommendation, selected_yes_price, selected_no_price,
                    selected_market_json, runtime_snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_now_iso(),
                    title_id,
                    target_title,
                    selected_ticker,
                    selected_title,
                    str(market.get("market_type") or ""),
                    str(market.get("comparator") or ""),
                    market.get("threshold"),
                    market.get("range_low"),
                    market.get("range_high"),
                    runtime_snapshot.get("calculated_tomatometer"),
                    int(runtime_snapshot.get("system_review_count", 0)),
                    float(recommendation["model_prob"]),
                    float(recommendation["market_prob"]),
                    float(recommendation["edge"]),
                    str(recommendation["recommendation"]),
                    yes_price,
                    no_price,
                    json.dumps(selected_market, ensure_ascii=True),
                    json.dumps(runtime_snapshot, ensure_ascii=True),
                ),
            )
            snapshot_id = int(cursor.lastrowid)
            for live_market in live_markets:
                conn.execute(
                    """
                    INSERT INTO market_quote_snapshots (
                        signal_snapshot_id, recorded_at, title_id, target_title, market_ticker, market_title,
                        yes_bid, yes_ask, no_bid, no_ask, market_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        _utc_now_iso(),
                        title_id,
                        target_title,
                        str(live_market.get("ticker") or ""),
                        str(live_market.get("title") or live_market.get("subtitle") or ""),
                        live_market.get("yes_bid"),
                        live_market.get("yes_ask"),
                        live_market.get("no_bid"),
                        live_market.get("no_ask"),
                        json.dumps(live_market, ensure_ascii=True),
                    ),
                )
            conn.commit()
        return snapshot_id

    def append_order_intent(
        self,
        *,
        target_title: str,
        market_ticker: str,
        side: str,
        action: str,
        count: int,
        limit_price: Optional[float],
        strategy_key: str,
        status: str = "planned",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        title_id = slugify_title(target_title)
        with self._write_lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO order_intents (
                    recorded_at, title_id, target_title, market_ticker, side, action, count,
                    limit_price, strategy_key, status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_now_iso(),
                    title_id,
                    target_title,
                    market_ticker,
                    side.upper(),
                    action.upper(),
                    int(count),
                    limit_price,
                    strategy_key,
                    status,
                    json.dumps(metadata or {}, ensure_ascii=True),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def replace_simulated_order_plan(
        self,
        *,
        target_title: str,
        strategy_key: str,
        orders: Sequence[Dict[str, Any]],
        signal_snapshot_id: Optional[int] = None,
        status: str = "planned",
    ) -> List[int]:
        title_id = slugify_title(target_title)
        metadata_base = {"signal_snapshot_id": signal_snapshot_id} if signal_snapshot_id is not None else {}
        inserted_ids: List[int] = []
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "DELETE FROM order_intents WHERE title_id = ? AND strategy_key = ? AND status = ?",
                (title_id, strategy_key, status),
            )
            for order in orders:
                metadata = dict(metadata_base)
                metadata.update(
                    {
                        "title": order.get("title"),
                        "expected_edge": order.get("expected_edge"),
                        "contract_type": order.get("contract_type"),
                        "model_probability_for_side": order.get("model_probability_for_side"),
                        "market_buy_price": order.get("market_buy_price"),
                        "lower_bound": order.get("lower_bound"),
                        "upper_bound": order.get("upper_bound"),
                    }
                )
                cursor = conn.execute(
                    """
                    INSERT INTO order_intents (
                        recorded_at, title_id, target_title, market_ticker, side, action, count,
                        limit_price, strategy_key, status, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _utc_now_iso(),
                        title_id,
                        target_title,
                        str(order.get("ticker") or ""),
                        str(order.get("side") or "").upper(),
                        str(order.get("action") or "BUY").upper(),
                        int(order.get("count") or 0),
                        order.get("limit_price"),
                        strategy_key,
                        status,
                        json.dumps(metadata, ensure_ascii=True),
                    ),
                )
                inserted_ids.append(int(cursor.lastrowid))
            conn.commit()
        return inserted_ids

    def record_market_quote_snapshot(
        self,
        *,
        target_title: str,
        markets: Sequence[Dict[str, Any]],
        signal_snapshot_id: Optional[int] = None,
    ) -> int:
        title_id = slugify_title(target_title)
        inserted = 0
        with self._write_lock, self._connect() as conn:
            for market in markets:
                conn.execute(
                    """
                    INSERT INTO market_quote_snapshots (
                        signal_snapshot_id, recorded_at, title_id, target_title, market_ticker, market_title,
                        yes_bid, yes_ask, no_bid, no_ask, market_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(signal_snapshot_id or 0),
                        _utc_now_iso(),
                        title_id,
                        target_title,
                        str(market.get("ticker") or ""),
                        str(market.get("title") or market.get("subtitle") or ""),
                        market.get("yes_bid"),
                        market.get("yes_ask"),
                        market.get("no_bid"),
                        market.get("no_ask"),
                        json.dumps(dict(market), ensure_ascii=True),
                    ),
                )
                inserted += 1
            conn.commit()
        return inserted

    def append_order_record(
        self,
        *,
        target_title: str,
        market_ticker: str,
        order_id: str,
        client_order_id: Optional[str],
        side: str,
        action: str,
        count: int,
        yes_price: Optional[float],
        no_price: Optional[float],
        status: str,
        payload: Dict[str, Any],
        intent_id: Optional[int] = None,
        dry_run: bool = False,
    ) -> int:
        title_id = slugify_title(target_title)
        with self._write_lock, self._connect() as conn:
            existing_id = self._find_existing_order_row_id(conn, order_id=order_id, client_order_id=client_order_id)
            timestamp = _utc_now_iso()
            if existing_id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO orders (
                        recorded_at, updated_at, title_id, target_title, market_ticker, order_id, client_order_id,
                        intent_id, side, action, count, yes_price, no_price, status, dry_run, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        timestamp,
                        title_id,
                        target_title,
                        market_ticker,
                        order_id,
                        client_order_id,
                        intent_id,
                        side.upper(),
                        action.upper(),
                        int(count),
                        yes_price,
                        no_price,
                        status,
                        1 if dry_run else 0,
                        json.dumps(payload, ensure_ascii=True),
                    ),
                )
                row_id = int(cursor.lastrowid)
            else:
                conn.execute(
                    """
                    UPDATE orders SET
                        updated_at = ?,
                        title_id = ?,
                        target_title = ?,
                        market_ticker = ?,
                        order_id = ?,
                        client_order_id = ?,
                        intent_id = COALESCE(?, intent_id),
                        side = ?,
                        action = ?,
                        count = ?,
                        yes_price = ?,
                        no_price = ?,
                        status = ?,
                        dry_run = ?,
                        payload_json = ?
                    WHERE id = ?
                    """,
                    (
                        timestamp,
                        title_id,
                        target_title,
                        market_ticker,
                        order_id,
                        client_order_id,
                        intent_id,
                        side.upper(),
                        action.upper(),
                        int(count),
                        yes_price,
                        no_price,
                        status,
                        1 if dry_run else 0,
                        json.dumps(payload, ensure_ascii=True),
                        existing_id,
                    ),
                )
                row_id = existing_id
            conn.commit()
            return row_id

    def append_fill(
        self,
        *,
        target_title: str,
        market_ticker: str,
        order_id: Optional[str],
        side: str,
        count: int,
        price: float,
        fee: float = 0.0,
        payload: Optional[Dict[str, Any]] = None,
        external_fill_id: Optional[str] = None,
    ) -> int:
        title_id = slugify_title(target_title)
        with self._write_lock, self._connect() as conn:
            existing_id = self._find_existing_fill_row_id(conn, external_fill_id=external_fill_id)
            if existing_id is not None:
                return existing_id
            cursor = conn.execute(
                """
                INSERT INTO fills (
                    recorded_at, title_id, target_title, market_ticker, order_id, side, count, price, fee, external_fill_id, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_now_iso(),
                    title_id,
                    target_title,
                    market_ticker,
                    order_id,
                    side.upper(),
                    int(count),
                    float(price),
                    float(fee),
                    external_fill_id,
                    json.dumps(payload or {}, ensure_ascii=True),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def load_order_intents(
        self,
        *,
        status: Optional[str] = None,
        target_title: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[OrderIntentRecord]:
        query = "SELECT id, recorded_at, title_id, target_title, market_ticker, side, action, count, limit_price, strategy_key, status, metadata_json FROM order_intents WHERE 1=1"
        params: List[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if target_title:
            query += " AND title_id = ?"
            params.append(slugify_title(target_title))
        if market_ticker:
            query += " AND market_ticker = ?"
            params.append(market_ticker)
        query += " ORDER BY id ASC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_order_intent(row) for row in rows]

    def get_order_intent(self, intent_id: int) -> Optional[OrderIntentRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, recorded_at, title_id, target_title, market_ticker, side, action, count, limit_price, strategy_key, status, metadata_json FROM order_intents WHERE id = ?",
                (int(intent_id),),
            ).fetchone()
        return None if row is None else self._row_to_order_intent(row)

    def update_order_intent_status(
        self,
        intent_id: int,
        *,
        status: str,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._write_lock, self._connect() as conn:
            row = conn.execute("SELECT metadata_json FROM order_intents WHERE id = ?", (int(intent_id),)).fetchone()
            metadata = json.loads(row[0]) if row and row[0] else {}
            metadata.update(metadata_updates or {})
            conn.execute(
                "UPDATE order_intents SET status = ?, metadata_json = ? WHERE id = ?",
                (status, json.dumps(metadata, ensure_ascii=True), int(intent_id)),
            )
            conn.commit()

    def get_order_by_client_order_id(self, client_order_id: str) -> Optional[Dict[str, Any]]:
        return self._get_order_record("client_order_id = ?", [client_order_id])

    def get_order_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self._get_order_record("order_id = ?", [order_id])

    def load_orders(
        self,
        *,
        target_title: Optional[str] = None,
        market_ticker: Optional[str] = None,
        status: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT id, recorded_at, updated_at, title_id, target_title, market_ticker, order_id, client_order_id,
                   intent_id, side, action, count, yes_price, no_price, status, dry_run, payload_json
            FROM orders
            WHERE 1=1
        """
        params: List[Any] = []
        if target_title:
            query += " AND title_id = ?"
            params.append(slugify_title(target_title))
        if market_ticker:
            query += " AND market_ticker = ?"
            params.append(market_ticker)
        if status:
            query += " AND status = ?"
            params.append(status)
        if dry_run is not None:
            query += " AND dry_run = ?"
            params.append(1 if dry_run else 0)
        query += " ORDER BY id ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._order_row_to_dict(row) for row in rows]

    def get_latest_signal_snapshot(self, target_title: str) -> Optional[Dict[str, Any]]:
        frame = self.load_signal_history(target_title)
        if frame.empty:
            return None
        latest = frame.iloc[-1].to_dict()
        return latest

    def set_paper_trading_state(
        self,
        *,
        target_title: str,
        enabled: bool,
        kalshi_link: Optional[str] = None,
        poll_interval_seconds: Optional[int] = None,
        status: Optional[str] = None,
        last_error: Optional[str] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
        heartbeat: bool = False,
        cycle_completed: bool = False,
    ) -> PaperTradingState:
        title_id = slugify_title(target_title)
        existing = self.get_paper_trading_state(target_title) or PaperTradingState(
            title_id=title_id,
            target_title=target_title,
            enabled=False,
            kalshi_link="",
            poll_interval_seconds=30,
            status="stopped",
            last_error=None,
            last_started_at=None,
            last_stopped_at=None,
            last_heartbeat_at=None,
            last_cycle_at=None,
            metadata={},
        )
        metadata = dict(existing.metadata)
        metadata.update(metadata_updates or {})
        now = _utc_now_iso()
        payload = PaperTradingState(
            title_id=title_id,
            target_title=target_title,
            enabled=enabled,
            kalshi_link=kalshi_link if kalshi_link is not None else existing.kalshi_link,
            poll_interval_seconds=int(poll_interval_seconds if poll_interval_seconds is not None else existing.poll_interval_seconds),
            status=status or existing.status,
            last_error=last_error if last_error is not None else existing.last_error,
            last_started_at=existing.last_started_at,
            last_stopped_at=existing.last_stopped_at,
            last_heartbeat_at=existing.last_heartbeat_at,
            last_cycle_at=existing.last_cycle_at,
            metadata=metadata,
        )
        if enabled and existing.enabled is False:
            payload.last_started_at = now
        if not enabled:
            payload.last_stopped_at = now
        if heartbeat:
            payload.last_heartbeat_at = now
        if cycle_completed:
            payload.last_cycle_at = now
        with self._write_lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO paper_trading_state (
                    title_id, target_title, enabled, kalshi_link, poll_interval_seconds, status, last_error,
                    last_started_at, last_stopped_at, last_heartbeat_at, last_cycle_at, metadata_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title_id) DO UPDATE SET
                    target_title=excluded.target_title,
                    enabled=excluded.enabled,
                    kalshi_link=excluded.kalshi_link,
                    poll_interval_seconds=excluded.poll_interval_seconds,
                    status=excluded.status,
                    last_error=excluded.last_error,
                    last_started_at=excluded.last_started_at,
                    last_stopped_at=excluded.last_stopped_at,
                    last_heartbeat_at=excluded.last_heartbeat_at,
                    last_cycle_at=excluded.last_cycle_at,
                    metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
                """,
                (
                    payload.title_id,
                    payload.target_title,
                    1 if payload.enabled else 0,
                    payload.kalshi_link,
                    payload.poll_interval_seconds,
                    payload.status,
                    payload.last_error,
                    payload.last_started_at,
                    payload.last_stopped_at,
                    payload.last_heartbeat_at,
                    payload.last_cycle_at,
                    json.dumps(payload.metadata, ensure_ascii=True),
                    now,
                ),
            )
            conn.commit()
        return payload

    def get_paper_trading_state(self, target_title: str) -> Optional[PaperTradingState]:
        title_id = slugify_title(target_title)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT title_id, target_title, enabled, kalshi_link, poll_interval_seconds, status, last_error,
                       last_started_at, last_stopped_at, last_heartbeat_at, last_cycle_at, metadata_json
                FROM paper_trading_state
                WHERE title_id = ?
                """,
                (title_id,),
            ).fetchone()
        if row is None:
            return None
        return PaperTradingState(
            title_id=str(row["title_id"]),
            target_title=str(row["target_title"]),
            enabled=bool(row["enabled"]),
            kalshi_link=str(row["kalshi_link"] or ""),
            poll_interval_seconds=int(row["poll_interval_seconds"] or 30),
            status=str(row["status"] or "stopped"),
            last_error=None if row["last_error"] is None else str(row["last_error"]),
            last_started_at=None if row["last_started_at"] is None else str(row["last_started_at"]),
            last_stopped_at=None if row["last_stopped_at"] is None else str(row["last_stopped_at"]),
            last_heartbeat_at=None if row["last_heartbeat_at"] is None else str(row["last_heartbeat_at"]),
            last_cycle_at=None if row["last_cycle_at"] is None else str(row["last_cycle_at"]),
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
        )

    def load_signal_history(self, target_title: str, market_ticker: Optional[str] = None) -> pd.DataFrame:
        title_id = slugify_title(target_title)
        query = "SELECT * FROM signal_snapshots WHERE title_id = ?"
        params: List[Any] = [title_id]
        if market_ticker:
            query += " AND market_ticker = ?"
            params.append(market_ticker)
        query += " ORDER BY id ASC"
        with self._connect() as conn:
            frame = pd.read_sql_query(query, conn, params=params)
        if frame.empty:
            return frame
        frame["recorded_at"] = pd.to_datetime(frame["recorded_at"], utc=True, errors="coerce")
        return frame

    def load_quote_history(self, target_title: str, market_ticker: Optional[str] = None) -> pd.DataFrame:
        title_id = slugify_title(target_title)
        query = "SELECT * FROM market_quote_snapshots WHERE title_id = ?"
        params: List[Any] = [title_id]
        if market_ticker:
            query += " AND market_ticker = ?"
            params.append(market_ticker)
        query += " ORDER BY id ASC"
        with self._connect() as conn:
            frame = pd.read_sql_query(query, conn, params=params)
        if frame.empty:
            return frame
        frame["recorded_at"] = pd.to_datetime(frame["recorded_at"], utc=True, errors="coerce")
        return frame

    def build_simulated_pnl_frame(self, target_title: str, market_ticker: Optional[str] = None) -> pd.DataFrame:
        simulated_plan_frame = self._build_simulated_order_plan_frame(target_title)
        if not simulated_plan_frame.empty:
            return simulated_plan_frame
        frame = self.load_signal_history(target_title, market_ticker=market_ticker)
        if frame.empty:
            return frame

        cumulative_pnl = 0.0
        trade_pnls: List[float] = []
        cumulative_pnls: List[float] = []
        for _, row in frame.iterrows():
            model_prob = float(row["model_prob"])
            yes_price = row["selected_yes_price"]
            no_price = row["selected_no_price"]
            side = str(row["recommendation"] or "NO TRADE")
            if side == "BUY YES" and yes_price is not None:
                trade_pnl = model_prob - float(yes_price)
            elif side == "BUY NO" and no_price is not None:
                trade_pnl = (1.0 - model_prob) - float(no_price)
            else:
                trade_pnl = 0.0
            cumulative_pnl += trade_pnl
            trade_pnls.append(trade_pnl)
            cumulative_pnls.append(cumulative_pnl)

        enriched = frame.copy()
        enriched["trade_pnl"] = trade_pnls
        enriched["cumulative_pnl"] = cumulative_pnls
        return enriched

    def _build_simulated_order_plan_frame(self, target_title: str) -> pd.DataFrame:
        intents = self.load_order_intents(status="planned", target_title=target_title)
        if not intents:
            return pd.DataFrame()
        quotes = self.load_quote_history(target_title)
        if quotes.empty:
            return pd.DataFrame()

        intent_rows = []
        for intent in intents:
            intent_rows.append(
                {
                    "recorded_at": pd.to_datetime(intent.recorded_at, utc=True, errors="coerce"),
                    "market_ticker": intent.market_ticker,
                    "side": intent.side.upper(),
                    "count": int(intent.count),
                    "limit_price": None if intent.limit_price is None else float(intent.limit_price),
                    "strategy_key": intent.strategy_key,
                    "metadata": dict(intent.metadata),
                }
            )
        intent_frame = pd.DataFrame(intent_rows).dropna(subset=["recorded_at"])
        if intent_frame.empty:
            return pd.DataFrame()

        records: List[Dict[str, Any]] = []
        quote_frame = quotes.sort_values("recorded_at")
        for timestamp in sorted(quote_frame["recorded_at"].dropna().unique()):
            active_intents = intent_frame[intent_frame["recorded_at"] <= timestamp]
            if active_intents.empty:
                continue
            total_pnl = 0.0
            dominant_recommendation = "NO TRADE"
            dominant_edge = 0.0
            for _, intent in active_intents.iterrows():
                market_quotes = quote_frame[
                    (quote_frame["market_ticker"] == intent["market_ticker"]) &
                    (quote_frame["recorded_at"] <= timestamp)
                ]
                if market_quotes.empty or intent["limit_price"] is None:
                    continue
                latest_quote = market_quotes.iloc[-1]
                if intent["side"] == "YES":
                    mark_price = latest_quote.get("yes_bid")
                    recommendation = "BUY YES"
                else:
                    mark_price = latest_quote.get("no_bid")
                    recommendation = "BUY NO"
                if mark_price is None:
                    continue
                edge = float(intent["metadata"].get("expected_edge") or 0.0)
                pnl = (float(mark_price) - float(intent["limit_price"])) * int(intent["count"])
                total_pnl += pnl
                if abs(edge) >= abs(dominant_edge):
                    dominant_edge = edge
                    dominant_recommendation = recommendation
            records.append(
                {
                    "recorded_at": timestamp,
                    "cumulative_pnl": total_pnl,
                    "edge": dominant_edge,
                    "recommendation": dominant_recommendation,
                }
            )
        return pd.DataFrame(records)

    def get_position_summary(self, target_title: str, market_ticker: str) -> PositionSummary:
        title_id = slugify_title(target_title)
        with self._connect() as conn:
            fills = pd.read_sql_query(
                "SELECT side, count, price, fee FROM fills WHERE title_id = ? AND market_ticker = ? ORDER BY id ASC",
                conn,
                params=[title_id, market_ticker],
            )
        if fills.empty:
            return PositionSummary(title_id=title_id, market_ticker=market_ticker, yes_contracts=0, no_contracts=0, net_cost=0.0, realized_pnl=0.0)

        yes_contracts = 0
        no_contracts = 0
        net_cost = 0.0
        for _, row in fills.iterrows():
            side = str(row["side"]).upper()
            count = int(row["count"])
            price = float(row["price"])
            fee = float(row["fee"])
            net_cost += (price * count) + fee
            if side == "YES":
                yes_contracts += count
            elif side == "NO":
                no_contracts += count
        return PositionSummary(
            title_id=title_id,
            market_ticker=market_ticker,
            yes_contracts=yes_contracts,
            no_contracts=no_contracts,
            net_cost=net_cost,
            realized_pnl=0.0,
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS signal_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    title_id TEXT NOT NULL,
                    target_title TEXT NOT NULL,
                    market_ticker TEXT NOT NULL,
                    market_title TEXT NOT NULL,
                    market_type TEXT NOT NULL,
                    comparator TEXT,
                    threshold REAL,
                    range_low REAL,
                    range_high REAL,
                    predicted_rt REAL,
                    system_review_count INTEGER NOT NULL,
                    model_prob REAL NOT NULL,
                    market_prob REAL NOT NULL,
                    edge REAL NOT NULL,
                    recommendation TEXT NOT NULL,
                    selected_yes_price REAL,
                    selected_no_price REAL,
                    selected_market_json TEXT NOT NULL,
                    runtime_snapshot_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_signal_snapshots_title_market_time
                ON signal_snapshots(title_id, market_ticker, recorded_at);

                CREATE TABLE IF NOT EXISTS market_quote_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_snapshot_id INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL,
                    title_id TEXT NOT NULL,
                    target_title TEXT NOT NULL,
                    market_ticker TEXT NOT NULL,
                    market_title TEXT NOT NULL,
                    yes_bid REAL,
                    yes_ask REAL,
                    no_bid REAL,
                    no_ask REAL,
                    market_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_market_quote_snapshots_title_market_time
                ON market_quote_snapshots(title_id, market_ticker, recorded_at);

                CREATE TABLE IF NOT EXISTS order_intents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    title_id TEXT NOT NULL,
                    target_title TEXT NOT NULL,
                    market_ticker TEXT NOT NULL,
                    side TEXT NOT NULL,
                    action TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    limit_price REAL,
                    strategy_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_order_intents_status_time
                ON order_intents(status, recorded_at);

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title_id TEXT NOT NULL,
                    target_title TEXT NOT NULL,
                    market_ticker TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    client_order_id TEXT,
                    intent_id INTEGER,
                    side TEXT NOT NULL,
                    action TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    yes_price REAL,
                    no_price REAL,
                    status TEXT NOT NULL,
                    dry_run INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_orders_title_market_time
                ON orders(title_id, market_ticker, recorded_at);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_client_order_id_unique
                ON orders(client_order_id)
                WHERE client_order_id IS NOT NULL;
                CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_order_id_unique
                ON orders(order_id);

                CREATE TABLE IF NOT EXISTS fills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    title_id TEXT NOT NULL,
                    target_title TEXT NOT NULL,
                    market_ticker TEXT NOT NULL,
                    order_id TEXT,
                    side TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    price REAL NOT NULL,
                    fee REAL NOT NULL,
                    external_fill_id TEXT,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_fills_title_market_time
                ON fills(title_id, market_ticker, recorded_at);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_fills_external_fill_id_unique
                ON fills(external_fill_id)
                WHERE external_fill_id IS NOT NULL;

                CREATE TABLE IF NOT EXISTS paper_trading_state (
                    title_id TEXT PRIMARY KEY,
                    target_title TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    kalshi_link TEXT NOT NULL,
                    poll_interval_seconds INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    last_error TEXT,
                    last_started_at TEXT,
                    last_stopped_at TEXT,
                    last_heartbeat_at TEXT,
                    last_cycle_at TEXT,
                    metadata_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self._migrate_schema(conn)
            conn.commit()

    def _migrate_schema(self, conn: sqlite3.Connection) -> None:
        self._ensure_column(conn, "orders", "updated_at", "TEXT")
        self._ensure_column(conn, "orders", "intent_id", "INTEGER")
        self._ensure_column(conn, "orders", "dry_run", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_column(conn, "fills", "external_fill_id", "TEXT")

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {str(row[1]) for row in rows}
        if column in existing:
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

    def _row_to_order_intent(self, row: Sequence[Any]) -> OrderIntentRecord:
        return OrderIntentRecord(
            id=int(row[0]),
            recorded_at=str(row[1]),
            title_id=str(row[2]),
            target_title=str(row[3]),
            market_ticker=str(row[4]),
            side=str(row[5]),
            action=str(row[6]),
            count=int(row[7]),
            limit_price=None if row[8] is None else float(row[8]),
            strategy_key=str(row[9]),
            status=str(row[10]),
            metadata=json.loads(row[11]) if row[11] else {},
        )

    def _get_order_record(self, where_clause: str, params: List[Any]) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT id, recorded_at, updated_at, title_id, target_title, market_ticker, order_id, client_order_id,
                       intent_id, side, action, count, yes_price, no_price, status, dry_run, payload_json
                FROM orders
                WHERE {where_clause}
                LIMIT 1
                """,
                params,
            ).fetchone()
        if row is None:
            return None
        return self._order_row_to_dict(row)

    def _order_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"]),
            "recorded_at": str(row["recorded_at"]),
            "updated_at": str(row["updated_at"]),
            "title_id": str(row["title_id"]),
            "target_title": str(row["target_title"]),
            "market_ticker": str(row["market_ticker"]),
            "order_id": str(row["order_id"]),
            "client_order_id": None if row["client_order_id"] is None else str(row["client_order_id"]),
            "intent_id": row["intent_id"],
            "side": str(row["side"]),
            "action": str(row["action"]),
            "count": int(row["count"]),
            "yes_price": None if row["yes_price"] is None else float(row["yes_price"]),
            "no_price": None if row["no_price"] is None else float(row["no_price"]),
            "status": str(row["status"]),
            "dry_run": bool(row["dry_run"]),
            "payload": json.loads(row["payload_json"]) if row["payload_json"] else {},
        }

    def _find_existing_order_row_id(
        self,
        conn: sqlite3.Connection,
        *,
        order_id: str,
        client_order_id: Optional[str],
    ) -> Optional[int]:
        if client_order_id:
            row = conn.execute("SELECT id FROM orders WHERE client_order_id = ? LIMIT 1", (client_order_id,)).fetchone()
            if row is not None:
                return int(row[0])
        row = conn.execute("SELECT id FROM orders WHERE order_id = ? LIMIT 1", (order_id,)).fetchone()
        if row is not None:
            return int(row[0])
        return None

    def _find_existing_fill_row_id(self, conn: sqlite3.Connection, *, external_fill_id: Optional[str]) -> Optional[int]:
        if not external_fill_id:
            return None
        row = conn.execute("SELECT id FROM fills WHERE external_fill_id = ? LIMIT 1", (external_fill_id,)).fetchone()
        if row is None:
            return None
        return int(row[0])

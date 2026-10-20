from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from market.kalshi_client import KalshiClient
from market.trade_ledger import OrderIntentRecord, TradeLedger


@dataclass
class ExecutionOutcome:
    intent_id: int
    client_order_id: str
    status: str
    order_id: Optional[str]
    dry_run: bool
    payload: Dict[str, Any]


def build_client_order_id(intent: OrderIntentRecord) -> str:
    digest = hashlib.sha256(
        "|".join(
            [
                str(intent.id),
                intent.target_title,
                intent.market_ticker,
                intent.side.upper(),
                intent.action.upper(),
                str(intent.count),
                str(intent.limit_price),
                intent.strategy_key,
            ]
        ).encode("utf-8")
    ).hexdigest()[:20]
    return f"rtkp-{intent.id}-{digest}"


def build_paper_client_order_id(
    *,
    target_title: str,
    market_ticker: str,
    side: str,
    action: str,
    strategy_key: str,
) -> str:
    digest = hashlib.sha256(
        "|".join(
            [
                target_title,
                market_ticker,
                side.upper(),
                action.upper(),
                strategy_key,
            ]
        ).encode("utf-8")
    ).hexdigest()[:20]
    return f"paper-{digest}"


class KalshiExecutor:
    def __init__(
        self,
        *,
        ledger: TradeLedger,
        client: KalshiClient,
        dry_run: bool = False,
    ) -> None:
        self.ledger = ledger
        self.client = client
        self.dry_run = dry_run

    def submit_planned_intents(self, *, limit: Optional[int] = None) -> List[ExecutionOutcome]:
        intents = self.ledger.load_order_intents(status="planned", limit=limit)
        return [self.submit_intent(intent.id) for intent in intents]

    def submit_intent(self, intent_id: int) -> ExecutionOutcome:
        intent = self._require_intent(intent_id)
        client_order_id = self._get_or_build_client_order_id(intent)
        existing_order = self.ledger.get_order_by_client_order_id(client_order_id)
        if existing_order is not None:
            self.ledger.update_order_intent_status(
                intent.id,
                status="submitted" if not existing_order.get("dry_run") else "dry_run",
                metadata_updates={
                    "client_order_id": client_order_id,
                    "order_id": existing_order.get("order_id"),
                    "reused_existing_order": True,
                },
            )
            return ExecutionOutcome(
                intent_id=intent.id,
                client_order_id=client_order_id,
                status=str(existing_order.get("status") or ""),
                order_id=existing_order.get("order_id"),
                dry_run=bool(existing_order.get("dry_run")),
                payload=dict(existing_order.get("payload") or {}),
            )

        if self.dry_run:
            payload = self._build_dry_run_payload(intent, client_order_id)
            order_id = f"dryrun-{client_order_id}"
            self.ledger.append_order_record(
                target_title=intent.target_title,
                market_ticker=intent.market_ticker,
                order_id=order_id,
                client_order_id=client_order_id,
                side=intent.side,
                action=intent.action,
                count=intent.count,
                yes_price=intent.limit_price if intent.side.upper() == "YES" else None,
                no_price=intent.limit_price if intent.side.upper() == "NO" else None,
                status="dry_run",
                payload=payload,
                intent_id=intent.id,
                dry_run=True,
            )
            self.ledger.update_order_intent_status(
                intent.id,
                status="dry_run",
                metadata_updates={"client_order_id": client_order_id, "order_id": order_id},
            )
            return ExecutionOutcome(
                intent_id=intent.id,
                client_order_id=client_order_id,
                status="dry_run",
                order_id=order_id,
                dry_run=True,
                payload=payload,
            )

        try:
            response = self.client.create_order(
                intent.market_ticker,
                side=intent.side,
                action=intent.action,
                count=intent.count,
                yes_price=intent.limit_price if intent.side.upper() == "YES" else None,
                no_price=intent.limit_price if intent.side.upper() == "NO" else None,
                client_order_id=client_order_id,
            )
            order_payload = dict(response.get("order") or response)
        except Exception as exc:
            order_payload = self._lookup_existing_order_payload(intent, client_order_id)
            if order_payload is None:
                self.ledger.update_order_intent_status(
                    intent.id,
                    status="submit_failed",
                    metadata_updates={
                        "client_order_id": client_order_id,
                        "last_error": str(exc),
                    },
                )
                raise

        persisted_order = self._persist_order_payload(intent, client_order_id, order_payload, dry_run=False)
        self.ledger.update_order_intent_status(
            intent.id,
            status="submitted",
            metadata_updates={"client_order_id": client_order_id, "order_id": persisted_order["order_id"]},
        )
        return ExecutionOutcome(
            intent_id=intent.id,
            client_order_id=client_order_id,
            status=str(persisted_order["status"]),
            order_id=str(persisted_order["order_id"]),
            dry_run=False,
            payload=order_payload,
        )

    def refresh_order(self, *, target_title: str, market_ticker: str, order_id: str) -> Dict[str, Any]:
        payload = self.client.get_order(order_id)
        side = str(payload.get("side") or "YES")
        action = str(payload.get("action") or "BUY")
        count = int(payload.get("count") or payload.get("remaining_count") or 0)
        persisted = self._persist_order_payload(
            OrderIntentRecord(
                id=0,
                recorded_at="",
                title_id="",
                target_title=target_title,
                market_ticker=market_ticker,
                side=side,
                action=action,
                count=count,
                limit_price=None,
                strategy_key="",
                status="submitted",
                metadata={},
            ),
            str(payload.get("client_order_id") or ""),
            payload,
            dry_run=False,
        )
        return persisted

    def cancel_order(self, *, intent_id: Optional[int] = None, order_id: Optional[str] = None) -> ExecutionOutcome:
        intent: Optional[OrderIntentRecord] = self.ledger.get_order_intent(intent_id) if intent_id is not None else None
        client_order_id = ""
        target_title = ""
        market_ticker = ""
        if order_id is None:
            if intent is None:
                raise ValueError("intent_id or order_id is required")
            client_order_id = self._get_or_build_client_order_id(intent)
            existing = self.ledger.get_order_by_client_order_id(client_order_id)
            if existing is None:
                raise ValueError(f"No persisted order found for intent {intent.id}")
            order_id = str(existing["order_id"])
            target_title = str(existing["target_title"])
            market_ticker = str(existing["market_ticker"])
        else:
            existing = self.ledger.get_order_by_order_id(order_id)
            if existing is not None:
                client_order_id = str(existing.get("client_order_id") or "")
                target_title = str(existing.get("target_title") or "")
                market_ticker = str(existing.get("market_ticker") or "")

        if self.dry_run:
            payload = {"order_id": order_id, "status": "canceled", "dry_run": True}
        else:
            response = self.client.cancel_order(order_id)
            payload = dict(response.get("order") or response)
        payload.setdefault("order_id", order_id)
        payload.setdefault("client_order_id", client_order_id or None)
        payload.setdefault("status", "canceled")
        persisted_id = self.ledger.append_order_record(
            target_title=target_title or (intent.target_title if intent else ""),
            market_ticker=market_ticker or (intent.market_ticker if intent else ""),
            order_id=str(payload.get("order_id") or order_id),
            client_order_id=str(payload.get("client_order_id") or client_order_id or "") or None,
            side=str(payload.get("side") or (intent.side if intent else "YES")),
            action=str(payload.get("action") or (intent.action if intent else "BUY")),
            count=int(payload.get("count") or payload.get("remaining_count") or (intent.count if intent else 0)),
            yes_price=self._extract_price(payload, "YES"),
            no_price=self._extract_price(payload, "NO"),
            status=str(payload.get("status") or "canceled"),
            payload=payload,
            intent_id=intent.id if intent else existing.get("intent_id") if existing else None,
            dry_run=self.dry_run,
        )
        if intent is not None:
            self.ledger.update_order_intent_status(intent.id, status="canceled", metadata_updates={"order_id": order_id})
        return ExecutionOutcome(
            intent_id=intent.id if intent else int(existing.get("intent_id") or 0) if existing else 0,
            client_order_id=str(payload.get("client_order_id") or client_order_id),
            status=str(payload.get("status") or "canceled"),
            order_id=str(payload.get("order_id") or order_id),
            dry_run=self.dry_run,
            payload={"ledger_order_row_id": persisted_id, **payload},
        )

    def _require_intent(self, intent_id: int) -> OrderIntentRecord:
        intent = self.ledger.get_order_intent(intent_id)
        if intent is None:
            raise ValueError(f"Unknown intent_id: {intent_id}")
        return intent

    def _get_or_build_client_order_id(self, intent: OrderIntentRecord) -> str:
        existing = intent.metadata.get("client_order_id")
        if existing:
            return str(existing)
        return build_client_order_id(intent)

    def _lookup_existing_order_payload(self, intent: OrderIntentRecord, client_order_id: str) -> Optional[Dict[str, Any]]:
        try:
            existing_orders = self.client.get_orders(client_order_id=client_order_id, ticker=intent.market_ticker, page_size=5, max_pages=1)
        except Exception:
            return None
        if not existing_orders:
            return None
        return dict(existing_orders[0])

    def _build_dry_run_payload(self, intent: OrderIntentRecord, client_order_id: str) -> Dict[str, Any]:
        return {
            "order_id": f"dryrun-{client_order_id}",
            "client_order_id": client_order_id,
            "ticker": intent.market_ticker,
            "side": intent.side.upper(),
            "action": intent.action.upper(),
            "count": intent.count,
            "status": "dry_run",
            "yes_price": intent.limit_price if intent.side.upper() == "YES" else None,
            "no_price": intent.limit_price if intent.side.upper() == "NO" else None,
        }

    def _persist_order_payload(
        self,
        intent: OrderIntentRecord,
        client_order_id: str,
        order_payload: Dict[str, Any],
        *,
        dry_run: bool,
    ) -> Dict[str, Any]:
        normalized = dict(order_payload)
        normalized.setdefault("client_order_id", client_order_id)
        normalized.setdefault("ticker", intent.market_ticker)
        normalized.setdefault("side", intent.side.upper())
        normalized.setdefault("action", intent.action.upper())
        normalized.setdefault("count", intent.count)
        normalized.setdefault("status", "accepted")
        order_id = str(normalized.get("order_id") or normalized.get("id") or normalized.get("order_uuid") or client_order_id)
        yes_price = self._extract_price(normalized, "YES")
        no_price = self._extract_price(normalized, "NO")
        self.ledger.append_order_record(
            target_title=intent.target_title,
            market_ticker=intent.market_ticker,
            order_id=order_id,
            client_order_id=client_order_id,
            side=str(normalized.get("side") or intent.side),
            action=str(normalized.get("action") or intent.action),
            count=int(normalized.get("count") or intent.count),
            yes_price=yes_price,
            no_price=no_price,
            status=str(normalized.get("status") or "accepted"),
            payload=normalized,
            intent_id=intent.id,
            dry_run=dry_run,
        )
        self._persist_fills(intent, order_id, normalized)
        persisted = self.ledger.get_order_by_client_order_id(client_order_id)
        if persisted is None:
            raise RuntimeError("Failed to persist order payload")
        return persisted

    def _persist_fills(self, intent: OrderIntentRecord, order_id: str, payload: Dict[str, Any]) -> None:
        fills = payload.get("fills")
        if not isinstance(fills, list):
            return
        for index, fill in enumerate(fills):
            if not isinstance(fill, dict):
                continue
            side = str(fill.get("side") or payload.get("side") or intent.side)
            count = int(fill.get("count") or fill.get("quantity") or fill.get("filled_count") or 0)
            if count <= 0:
                continue
            price = fill.get("price")
            if price is None:
                price = self._extract_price(fill, side)
            if price is None:
                continue
            fee = float(fill.get("fee") or 0.0)
            external_fill_id = str(fill.get("fill_id") or fill.get("id") or f"{order_id}:{index}")
            self.ledger.append_fill(
                target_title=intent.target_title,
                market_ticker=intent.market_ticker,
                order_id=order_id,
                side=side,
                count=count,
                price=float(price),
                fee=fee,
                payload=dict(fill),
                external_fill_id=external_fill_id,
            )

    def _extract_price(self, payload: Dict[str, Any], side: str) -> Optional[float]:
        normalized_side = side.upper()
        if normalized_side == "YES":
            keys = ("yes_price", "price", "limit_price")
        else:
            keys = ("no_price", "price", "limit_price")
        for key in keys:
            if payload.get(key) is None:
                continue
            value = float(payload[key])
            return value / 100.0 if value > 1.0 else value
        return None


class PaperTradingEngine:
    def __init__(self, *, ledger: TradeLedger, strategy_key: str = "paper_trading_plan") -> None:
        self.ledger = ledger
        self.strategy_key = strategy_key

    def sync_plan(
        self,
        *,
        target_title: str,
        plan_orders: Iterable[Dict[str, Any]],
        signal_snapshot_id: Optional[int] = None,
    ) -> List[int]:
        return self.ledger.replace_simulated_order_plan(
            target_title=target_title,
            strategy_key=self.strategy_key,
            orders=list(plan_orders),
            signal_snapshot_id=signal_snapshot_id,
            status="paper_planned",
        )

    def run_cycle(
        self,
        *,
        target_title: str,
        quote_markets: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        intents = self.ledger.load_order_intents(status="paper_planned", target_title=target_title)
        quote_map = {
            str(item.get("ticker") or ""): dict(item)
            for item in quote_markets
            if item.get("ticker")
        }
        if not intents:
            self._cancel_stale_resting_orders(target_title=target_title, active_client_order_ids=set())
            return {"planned_count": 0, "resting_count": 0, "filled_count": 0}

        active_keys = set()
        resting_count = 0
        filled_count = 0
        for intent in intents:
            order_record = self._ensure_paper_order(intent)
            active_keys.add(str(order_record.get("client_order_id") or ""))
            ticker = str(order_record.get("market_ticker") or intent.market_ticker)
            quote = quote_map.get(ticker)
            if quote is None:
                if str(order_record.get("status") or "") == "paper_resting":
                    resting_count += 1
                continue
            filled = self._attempt_fill(intent=intent, order_record=order_record, quote=quote)
            if filled:
                filled_count += 1
            elif str(self.ledger.get_order_by_client_order_id(str(order_record.get("client_order_id") or ""))["status"]) == "paper_resting":
                resting_count += 1

        self._cancel_stale_resting_orders(target_title=target_title, active_client_order_ids=active_keys)
        return {
            "planned_count": len(intents),
            "resting_count": resting_count,
            "filled_count": filled_count,
        }

    def _ensure_paper_order(self, intent: OrderIntentRecord) -> Dict[str, Any]:
        client_order_id = build_paper_client_order_id(
            target_title=intent.target_title,
            market_ticker=intent.market_ticker,
            side=intent.side,
            action=intent.action,
            strategy_key=self.strategy_key,
        )
        existing = self.ledger.get_order_by_client_order_id(client_order_id)
        payload = {
            "paper_trading": True,
            "strategy_key": self.strategy_key,
            "limit_price": intent.limit_price,
            "signal_snapshot_id": intent.metadata.get("signal_snapshot_id"),
            "expected_edge": intent.metadata.get("expected_edge"),
        }
        status = "paper_resting"
        order_id = f"paper-order-{client_order_id}"
        if existing is not None and str(existing.get("status") or "") == "paper_filled":
            status = "paper_filled"
            order_id = str(existing.get("order_id") or order_id)
        self.ledger.append_order_record(
            target_title=intent.target_title,
            market_ticker=intent.market_ticker,
            order_id=order_id,
            client_order_id=client_order_id,
            side=intent.side,
            action=intent.action,
            count=intent.count,
            yes_price=intent.limit_price if intent.side.upper() == "YES" else None,
            no_price=intent.limit_price if intent.side.upper() == "NO" else None,
            status=status,
            payload=payload,
            intent_id=intent.id,
            dry_run=True,
        )
        self.ledger.update_order_intent_status(
            intent.id,
            status="paper_submitted",
            metadata_updates={"client_order_id": client_order_id, "paper_order_id": order_id},
        )
        persisted = self.ledger.get_order_by_client_order_id(client_order_id)
        if persisted is None:
            raise RuntimeError("Failed to persist paper order")
        return persisted

    def _attempt_fill(
        self,
        *,
        intent: OrderIntentRecord,
        order_record: Dict[str, Any],
        quote: Dict[str, Any],
    ) -> bool:
        if str(order_record.get("status") or "") == "paper_filled":
            return False
        limit_price = intent.limit_price
        if limit_price is None:
            return False
        side = intent.side.upper()
        fill_price = quote.get("yes_ask") if side == "YES" else quote.get("no_ask")
        if fill_price is None or float(fill_price) > float(limit_price):
            return False
        order_id = str(order_record.get("order_id") or f"paper-order-{order_record.get('client_order_id')}")
        external_fill_id = f"{order_id}:fill"
        self.ledger.append_fill(
            target_title=intent.target_title,
            market_ticker=intent.market_ticker,
            order_id=order_id,
            side=side,
            count=int(intent.count),
            price=float(fill_price),
            fee=0.0,
            payload={"paper_trading": True, "quote": dict(quote)},
            external_fill_id=external_fill_id,
        )
        self.ledger.append_order_record(
            target_title=intent.target_title,
            market_ticker=intent.market_ticker,
            order_id=order_id,
            client_order_id=str(order_record.get("client_order_id") or ""),
            side=side,
            action=intent.action,
            count=int(intent.count),
            yes_price=float(fill_price) if side == "YES" else None,
            no_price=float(fill_price) if side == "NO" else None,
            status="paper_filled",
            payload={
                **dict(order_record.get("payload") or {}),
                "filled_at_price": float(fill_price),
                "paper_trading": True,
            },
            intent_id=order_record.get("intent_id"),
            dry_run=True,
        )
        self.ledger.update_order_intent_status(intent.id, status="paper_filled", metadata_updates={"fill_price": float(fill_price)})
        return True

    def _cancel_stale_resting_orders(self, *, target_title: str, active_client_order_ids: set[str]) -> None:
        resting_orders = self.ledger.load_orders(target_title=target_title, status="paper_resting", dry_run=True)
        for order in resting_orders:
            client_order_id = str(order.get("client_order_id") or "")
            if client_order_id in active_client_order_ids:
                continue
            self.ledger.append_order_record(
                target_title=str(order.get("target_title") or target_title),
                market_ticker=str(order.get("market_ticker") or ""),
                order_id=str(order.get("order_id") or ""),
                client_order_id=client_order_id or None,
                side=str(order.get("side") or "YES"),
                action=str(order.get("action") or "BUY"),
                count=int(order.get("count") or 0),
                yes_price=order.get("yes_price"),
                no_price=order.get("no_price"),
                status="paper_canceled",
                payload={**dict(order.get("payload") or {}), "paper_trading": True, "canceled_as_stale": True},
                intent_id=order.get("intent_id"),
                dry_run=True,
            )

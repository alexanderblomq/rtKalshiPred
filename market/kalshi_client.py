from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qs, unquote, urlencode, urlparse

from settings import KALSHI_API_BASE_URL

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover - environment dependent
    fuzz = None

try:
    import requests
except Exception:  # pragma: no cover - environment dependent
    requests = None

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except Exception:  # pragma: no cover - optional dependency in some environments
    hashes = None
    serialization = None
    padding = None


TICKER_RE = re.compile(r"^[A-Z0-9_\-]{3,}$")


def _normalize_text(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _looks_like_kalshi_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
    except Exception:
        return False
    hostname = (parsed.hostname or "").lower()
    return bool(parsed.scheme and hostname and "kalshi.com" in hostname)


def parse_kalshi_url(value: str) -> Dict[str, Any]:
    parsed = urlparse(value.strip())
    query = parse_qs(parsed.query)
    path_parts = [part for part in parsed.path.split("/") if part]

    query_candidates = []
    for key in ("ticker", "market_ticker", "event_ticker", "series_ticker"):
        query_candidates.extend(query.get(key, []))

    path_candidates = []
    for part in reversed(path_parts):
        clean = unquote(part).strip()
        if _looks_like_ticker(clean):
            path_candidates.append(clean)

    candidates = [candidate for candidate in query_candidates + path_candidates if candidate]
    ticker = next((candidate for candidate in candidates if _looks_like_ticker(candidate)), None)

    slug_candidate = None
    if path_parts:
        for part in reversed(path_parts):
            clean = unquote(part).strip()
            if clean and not _looks_like_ticker(clean):
                slug_candidate = clean
                break

    fallback_query = _normalize_text((slug_candidate or "").replace("-", " "))
    return {
        "url": value,
        "ticker": ticker,
        "event_ticker": next(iter(query.get("event_ticker", [])), None),
        "series_ticker": next(iter(query.get("series_ticker", [])), None),
        "search_text": fallback_query,
    }


def _looks_like_ticker(value: str) -> bool:
    return bool(TICKER_RE.fullmatch(value.strip()))


def _similarity(a: str, b: str) -> float:
    if a and a in b:
        return 100.0
    if fuzz is not None:
        return float(max(fuzz.token_set_ratio(a, b), fuzz.partial_ratio(a, b)))
    return float(difflib.SequenceMatcher(None, a, b).ratio() * 100.0)


def _to_dollars(value: Any) -> Optional[float]:
    if value is None:
        return None
    numeric = float(value)
    if numeric > 1.0:
        return round(numeric / 100.0, 4)
    return round(numeric, 4)


def _first_present(mapping: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _best_bid_from_orderbook_side(levels: Any) -> Optional[float]:
    if not isinstance(levels, list) or not levels:
        return None
    best_price: Optional[float] = None
    for level in levels:
        if not isinstance(level, (list, tuple)) or not level:
            continue
        price = _to_dollars(level[0])
        if price is None:
            continue
        if best_price is None or price > best_price:
            best_price = price
    return best_price


def normalize_market_payload(market: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(market)
    yes_bid = _to_dollars(
        _first_present(
            normalized,
            (
                "yes_bid",
                "yes_bid_dollars",
                "best_yes_bid",
                "last_price",
            ),
        )
    )
    no_bid = _to_dollars(
        _first_present(
            normalized,
            (
                "no_bid",
                "no_bid_dollars",
                "best_no_bid",
            ),
        )
    )
    yes_ask = _to_dollars(_first_present(normalized, ("yes_ask", "yes_ask_dollars", "best_yes_ask")))
    no_ask = _to_dollars(_first_present(normalized, ("no_ask", "no_ask_dollars", "best_no_ask")))

    orderbook = normalized.get("orderbook_fp") or normalized.get("orderbook")
    if isinstance(orderbook, dict):
        yes_bid = yes_bid if yes_bid is not None else _best_bid_from_orderbook_side(orderbook.get("yes_dollars"))
        no_bid = no_bid if no_bid is not None else _best_bid_from_orderbook_side(orderbook.get("no_dollars"))

    normalized["yes_bid"] = yes_bid
    normalized["no_bid"] = no_bid
    normalized["yes_ask"] = yes_ask if yes_ask is not None else (None if no_bid is None else round(1.0 - no_bid, 4))
    normalized["no_ask"] = no_ask if no_ask is not None else (None if yes_bid is None else round(1.0 - yes_bid, 4))
    return normalized


@dataclass
class KalshiCredentials:
    key_id: str
    private_key_pem: str

    @classmethod
    def from_env(cls) -> Optional["KalshiCredentials"]:
        key_id = os.getenv("KALSHI_API_KEY_ID")
        private_key = os.getenv("KALSHI_API_PRIVATE_KEY")
        private_key_path = os.getenv("KALSHI_API_PRIVATE_KEY_PATH")
        if not key_id:
            return None
        if private_key_path and not private_key:
            private_key = Path(private_key_path).read_text(encoding="utf-8")
        if not private_key:
            raise ValueError("Kalshi credentials require KALSHI_API_PRIVATE_KEY or KALSHI_API_PRIVATE_KEY_PATH")
        return cls(key_id=key_id, private_key_pem=private_key)


class KalshiClient:
    def __init__(
        self,
        base_url: str = KALSHI_API_BASE_URL,
        credentials: Optional[KalshiCredentials] = None,
        session: Optional[Any] = None,
        timeout_seconds: int = 20,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.credentials = credentials
        if session is not None:
            self.session = session
        else:
            if requests is None:
                raise RuntimeError("requests is required to construct a default KalshiClient session")
            self.session = requests.Session()
        self.timeout_seconds = timeout_seconds

    def get_exchange_status(self) -> Dict[str, Any]:
        return self._request("GET", "/exchange/status")

    def get_market(self, ticker: str) -> Dict[str, Any]:
        response = self._request("GET", f"/markets/{ticker}")
        return dict(response.get("market") or response)

    def get_markets(
        self,
        *,
        status: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        page_size: int = 100,
        max_pages: int = 1,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": page_size}
        if status:
            params["status"] = status
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker

        markets: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        for _ in range(max_pages):
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            response = self._request("GET", "/markets", params=page_params)
            page_markets = response.get("markets") or response.get("data") or []
            markets.extend(dict(item) for item in page_markets)
            cursor = response.get("cursor")
            if not cursor:
                break
        return markets

    def get_event(self, event_ticker: str, *, with_nested_markets: bool = False) -> Dict[str, Any]:
        response = self._request("GET", f"/events/{event_ticker}", params={"with_nested_markets": str(with_nested_markets).lower()})
        event = dict(response.get("event") or response)
        if with_nested_markets:
            nested_markets = event.get("markets") or response.get("markets") or []
            event["markets"] = [normalize_market_payload(dict(item)) for item in nested_markets]
        return event

    def get_events(
        self,
        *,
        status: Optional[str] = None,
        series_ticker: Optional[str] = None,
        with_nested_markets: bool = False,
        page_size: int = 200,
        max_pages: int = 1,
        min_updated_ts: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": page_size, "with_nested_markets": str(with_nested_markets).lower()}
        if status:
            params["status"] = status
        if series_ticker:
            params["series_ticker"] = series_ticker
        if min_updated_ts is not None:
            params["min_updated_ts"] = int(min_updated_ts)

        events: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        for _ in range(max_pages):
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            response = self._request("GET", "/events", params=page_params)
            page_events = response.get("events") or response.get("data") or []
            for item in page_events:
                event = dict(item)
                if with_nested_markets:
                    event["markets"] = [normalize_market_payload(dict(market)) for market in (event.get("markets") or [])]
                events.append(event)
            cursor = response.get("cursor")
            if not cursor:
                break
        return events

    def get_market_orderbook(self, ticker: str, depth: int = 10) -> Dict[str, Any]:
        response = self._request("GET", f"/markets/{ticker}/orderbook", params={"depth": depth})
        payload = response.get("orderbook") or response
        return dict(payload)

    def get_multiple_orderbooks(self, tickers: Iterable[str], depth: int = 10, max_workers: int = 8) -> Dict[str, Dict[str, Any]]:
        ticker_list = [str(ticker) for ticker in tickers]
        if not ticker_list:
            return {}
        orderbooks: Dict[str, Dict[str, Any]] = {}
        if self.credentials is not None:
            response = self._request(
                "GET",
                "/markets/orderbooks",
                params={"ticker": ticker_list, "depth": depth},
                auth_required=True,
            )
            for orderbook in response.get("orderbooks") or []:
                payload = dict(orderbook)
                ticker = str(payload.get("ticker") or "")
                if ticker:
                    orderbooks[ticker] = payload
            return orderbooks

        with ThreadPoolExecutor(max_workers=min(max_workers, len(ticker_list))) as executor:
            futures = {executor.submit(self.get_market_orderbook, ticker, depth=depth): ticker for ticker in ticker_list}
            for future in as_completed(futures):
                ticker = futures[future]
                orderbooks[ticker] = future.result()
        return orderbooks

    def get_balance(self) -> Dict[str, Any]:
        return self._request("GET", "/portfolio/balance", auth_required=True)

    def get_order(self, order_id: str) -> Dict[str, Any]:
        response = self._request("GET", f"/portfolio/orders/{order_id}", auth_required=True)
        return dict(response.get("order") or response)

    def get_orders(
        self,
        *,
        status: Optional[str] = None,
        ticker: Optional[str] = None,
        event_ticker: Optional[str] = None,
        client_order_id: Optional[str] = None,
        page_size: int = 100,
        max_pages: int = 1,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": page_size}
        if status:
            params["status"] = status
        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if client_order_id:
            params["client_order_id"] = client_order_id

        orders: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        for _ in range(max_pages):
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            response = self._request("GET", "/portfolio/orders", params=page_params, auth_required=True)
            page_orders = response.get("orders") or response.get("data") or []
            orders.extend(dict(item) for item in page_orders)
            cursor = response.get("cursor")
            if not cursor:
                break
        return orders

    def create_order(
        self,
        ticker: str,
        *,
        side: str,
        action: str,
        count: int,
        type_: str = "limit",
        yes_price: Optional[float] = None,
        no_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        expiration_ts: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "ticker": ticker,
            "side": side.upper(),
            "action": action.upper(),
            "count": int(count),
            "type": type_.lower(),
        }
        if client_order_id:
            payload["client_order_id"] = client_order_id
        if expiration_ts is not None:
            payload["expiration_ts"] = int(expiration_ts)
        if yes_price is not None:
            payload["yes_price"] = int(round(float(yes_price) * 100))
        if no_price is not None:
            payload["no_price"] = int(round(float(no_price) * 100))
        return self._request("POST", "/portfolio/orders", json=payload, auth_required=True)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/portfolio/orders/{order_id}", auth_required=True)

    def search_markets(self, market_input: str, *, status: str = "open", limit: int = 50) -> List[Dict[str, Any]]:
        normalized = _normalize_text(market_input)
        candidates = self.get_markets(status=status, page_size=min(200, max(limit * 3, 100)), max_pages=2)
        scored: List[tuple[float, Dict[str, Any]]] = []
        for market in candidates:
            haystack = _normalize_text(
                " ".join(
                    [
                        str(market.get("title") or ""),
                        str(market.get("subtitle") or ""),
                        str(market.get("ticker") or ""),
                    ]
                )
            )
            score = _similarity(normalized, haystack)
            if score < 45:
                continue
            scored.append((float(score), market))
        scored.sort(key=lambda item: (item[0], str(item[1].get("ticker") or "")), reverse=True)
        return [item[1] for item in scored[:limit]]

    def search_events(
        self,
        market_input: str,
        *,
        status: str = "open",
        limit: int = 25,
        series_ticker: Optional[str] = None,
        with_nested_markets: bool = True,
    ) -> List[Dict[str, Any]]:
        normalized = _normalize_text(market_input)
        candidates = self.get_events(
            status=status,
            series_ticker=series_ticker,
            with_nested_markets=with_nested_markets,
            page_size=min(200, max(limit * 4, 100)),
            max_pages=2,
        )
        scored: List[tuple[float, Dict[str, Any]]] = []
        for event in candidates:
            market_titles = " ".join(str(item.get("title") or item.get("subtitle") or "") for item in (event.get("markets") or []))
            haystack = _normalize_text(
                " ".join(
                    [
                        str(event.get("title") or ""),
                        str(event.get("sub_title") or ""),
                        str(event.get("event_ticker") or ""),
                        market_titles,
                    ]
                )
            )
            score = _similarity(normalized, haystack)
            if score < 45:
                continue
            scored.append((float(score), event))
        scored.sort(key=lambda item: (item[0], str(item[1].get("event_ticker") or "")), reverse=True)
        return [item[1] for item in scored[:limit]]

    def get_live_market_snapshot(
        self,
        market_input: str,
        *,
        status: str = "open",
        limit: int = 25,
        series_ticker: Optional[str] = None,
        include_orderbooks: bool = True,
        depth: int = 10,
    ) -> Dict[str, Any]:
        cleaned_input = market_input.strip()
        if _looks_like_ticker(cleaned_input):
            market = normalize_market_payload(self.get_market(cleaned_input))
            if include_orderbooks:
                try:
                    orderbook = self.get_market_orderbook(cleaned_input, depth=depth)
                    market = merge_market_with_orderbook(market, orderbook)
                except Exception:
                    pass
            return {
                "query": market_input,
                "match_type": "ticker",
                "event": None,
                "markets": [market],
            }

        events = self.search_events(
            cleaned_input,
            status=status,
            limit=max(5, limit),
            series_ticker=series_ticker,
            with_nested_markets=True,
        )
        if events:
            event = dict(events[0])
            markets = [normalize_market_payload(dict(item)) for item in (event.get("markets") or [])]
            if include_orderbooks and markets:
                markets = enrich_markets_with_orderbooks(self, markets, depth=depth)
                event["markets"] = markets
            return {
                "query": market_input,
                "match_type": "event",
                "event": event,
                "markets": markets,
            }

        markets = [normalize_market_payload(item) for item in self.search_markets(cleaned_input, status=status, limit=limit)]
        if include_orderbooks and markets:
            markets = enrich_markets_with_orderbooks(self, markets, depth=depth)
        return {
            "query": market_input,
            "match_type": "market_search",
            "event": None,
            "markets": markets,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        auth_required: bool = False,
    ) -> Dict[str, Any]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        full_path = f"{path}{query}"
        url = f"{self.base_url}{full_path}"
        headers = {"Accept": "application/json"}
        if auth_required:
            headers.update(self._build_auth_headers(method.upper(), full_path))
        response = self.session.request(
            method.upper(),
            url,
            headers=headers,
            json=json,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return dict(payload) if isinstance(payload, dict) else {"data": payload}

    def _build_auth_headers(self, method: str, path_with_query: str) -> Dict[str, str]:
        if self.credentials is None:
            env_credentials = KalshiCredentials.from_env()
            if env_credentials is None:
                raise ValueError("Authenticated Kalshi requests require credentials")
            self.credentials = env_credentials
        if serialization is None or hashes is None or padding is None:
            raise RuntimeError("cryptography is required for authenticated Kalshi requests")

        timestamp_ms = str(int(time.time() * 1000))
        message = f"{timestamp_ms}{method}{path_with_query}".encode("utf-8")
        private_key = serialization.load_pem_private_key(
            self.credentials.private_key_pem.encode("utf-8"),
            password=None,
        )
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return {
            "KALSHI-ACCESS-KEY": self.credentials.key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("ascii"),
        }


def fetch_market_contracts(
    market_input: str,
    *,
    client: Optional[KalshiClient] = None,
    status: str = "open",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    active_client = client or KalshiClient()
    cleaned_input = market_input.strip()
    if _looks_like_kalshi_url(cleaned_input):
        parsed = parse_kalshi_url(cleaned_input)
        if parsed["ticker"]:
            return [normalize_market_payload(active_client.get_market(parsed["ticker"]))]
        cleaned_input = parsed["search_text"] or cleaned_input
    if _looks_like_ticker(cleaned_input):
        return [normalize_market_payload(active_client.get_market(cleaned_input))]
    return [normalize_market_payload(item) for item in active_client.search_markets(cleaned_input, status=status, limit=limit)]


def fetch_live_market_snapshot(
    market_input: str,
    *,
    client: Optional[KalshiClient] = None,
    status: str = "open",
    limit: int = 25,
    series_ticker: Optional[str] = None,
    include_orderbooks: bool = True,
    depth: int = 10,
) -> Dict[str, Any]:
    active_client = client or KalshiClient()
    cleaned_input = market_input.strip()
    effective_series_ticker = series_ticker
    if _looks_like_kalshi_url(cleaned_input):
        parsed = parse_kalshi_url(cleaned_input)
        if parsed["ticker"]:
            return active_client.get_live_market_snapshot(
                parsed["ticker"],
                status=status,
                limit=limit,
                series_ticker=series_ticker,
                include_orderbooks=include_orderbooks,
                depth=depth,
            )
        cleaned_input = parsed["search_text"] or cleaned_input
        if effective_series_ticker is None:
            effective_series_ticker = parsed.get("series_ticker")
    return active_client.get_live_market_snapshot(
        cleaned_input,
        status=status,
        limit=limit,
        series_ticker=effective_series_ticker,
        include_orderbooks=include_orderbooks,
        depth=depth,
    )


def merge_market_with_orderbook(market: Dict[str, Any], orderbook: Dict[str, Any]) -> Dict[str, Any]:
    merged = normalize_market_payload(market)
    payload = dict(orderbook)
    merged["orderbook_fp"] = payload.get("orderbook_fp") or payload
    normalized = normalize_market_payload(merged)
    return normalized


def enrich_markets_with_orderbooks(
    client: KalshiClient,
    markets: Iterable[Dict[str, Any]],
    *,
    depth: int = 10,
) -> List[Dict[str, Any]]:
    market_list = [normalize_market_payload(dict(item)) for item in markets]
    tickers = [str(item.get("ticker") or "") for item in market_list if item.get("ticker")]
    if not tickers:
        return market_list
    try:
        orderbooks = client.get_multiple_orderbooks(tickers, depth=depth)
    except Exception:
        return market_list
    enriched: List[Dict[str, Any]] = []
    for market in market_list:
        ticker = str(market.get("ticker") or "")
        orderbook = orderbooks.get(ticker)
        if orderbook is None:
            enriched.append(market)
            continue
        enriched.append(merge_market_with_orderbook(market, orderbook))
    return enriched


def best_yes_buy_price(contract: Dict[str, Any]) -> Optional[float]:
    explicit = _to_dollars(_first_present(contract, ("yes_ask", "yes_ask_price", "yes_price", "best_yes_ask")))
    if explicit is not None:
        return explicit
    no_bid = _to_dollars(_first_present(contract, ("no_bid", "best_no_bid")))
    if no_bid is not None:
        return round(max(0.0, min(1.0, 1.0 - no_bid)), 4)
    return None


def best_no_buy_price(contract: Dict[str, Any]) -> Optional[float]:
    explicit = _to_dollars(_first_present(contract, ("no_ask", "no_ask_price", "no_price", "best_no_ask")))
    if explicit is not None:
        return explicit
    yes_bid = _to_dollars(_first_present(contract, ("yes_bid", "best_yes_bid")))
    if yes_bid is not None:
        return round(max(0.0, min(1.0, 1.0 - yes_bid)), 4)
    return None


def implied_probability_from_market(contract: Dict[str, Any], side: str = "yes") -> float:
    normalized_side = side.lower()
    if normalized_side == "yes":
        price = best_yes_buy_price(contract)
    elif normalized_side == "no":
        price = best_no_buy_price(contract)
    else:
        raise ValueError(f"Unsupported side: {side!r}")
    if price is None:
        fallback = _to_dollars(_first_present(contract, ("market_prob", f"{normalized_side}_price")))
        return float(fallback or 0.0)
    return float(price)

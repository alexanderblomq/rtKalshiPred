from __future__ import annotations

from dataclasses import dataclass

import pytest

from kalshi_client import (
    KalshiClient,
    best_no_buy_price,
    best_yes_buy_price,
    enrich_markets_with_orderbooks,
    fetch_market_contracts,
    fetch_live_market_snapshot,
    merge_market_with_orderbook,
    implied_probability_from_market,
    normalize_market_payload,
    parse_kalshi_url,
)


@dataclass
class FakeResponse:
    payload: dict
    status_code: int = 200

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, json=None, timeout=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "json": json,
                "timeout": timeout,
            }
        )
        return self.responses.pop(0)


def test_get_market_uses_market_payload():
    session = FakeSession([FakeResponse({"market": {"ticker": "KXTEST", "title": "Test market"}})])
    client = KalshiClient(base_url="https://api.example.test", session=session)

    market = client.get_market("KXTEST")

    assert market["ticker"] == "KXTEST"
    assert session.calls[0]["url"] == "https://api.example.test/markets/KXTEST"


def test_get_markets_paginates():
    session = FakeSession(
        [
            FakeResponse({"markets": [{"ticker": "FIRST"}], "cursor": "NEXT"}),
            FakeResponse({"markets": [{"ticker": "SECOND"}], "cursor": None}),
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session)

    markets = client.get_markets(status="open", page_size=1, max_pages=2)

    assert [item["ticker"] for item in markets] == ["FIRST", "SECOND"]
    assert session.calls[1]["url"].endswith("/markets?limit=1&status=open&cursor=NEXT")


def test_fetch_market_contracts_uses_search_for_non_ticker():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "markets": [
                        {"ticker": "RT_ANIMAL_FARM_70_79", "title": "Animal Farm 70%-79%"},
                        {"ticker": "OTHER", "title": "Other market"},
                    ],
                    "cursor": None,
                }
            )
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session)

    results = fetch_market_contracts("Animal Farm", client=client, limit=10)

    assert results[0]["ticker"] == "RT_ANIMAL_FARM_70_79"


def test_fetch_market_contracts_direct_ticker_path():
    session = FakeSession([FakeResponse({"market": {"ticker": "KXTEST"}})])
    client = KalshiClient(base_url="https://api.example.test", session=session)

    results = fetch_market_contracts("KXTEST", client=client)

    assert results[0]["ticker"] == "KXTEST"
    assert results[0]["yes_bid"] is None
    assert session.calls[0]["url"] == "https://api.example.test/markets/KXTEST"


def test_best_buy_prices_and_implied_probability():
    contract = {
        "yes_ask": 63,
        "yes_bid": 60,
    }

    assert best_yes_buy_price(contract) == 0.63
    assert best_no_buy_price(contract) == 0.4
    assert implied_probability_from_market(contract, side="yes") == 0.63
    assert implied_probability_from_market(contract, side="no") == 0.4


def test_authenticated_request_requires_credentials():
    client = KalshiClient(base_url="https://api.example.test", session=FakeSession([]))

    with pytest.raises(ValueError):
        client.get_balance()


def test_get_order_uses_order_payload(monkeypatch):
    session = FakeSession([FakeResponse({"order": {"order_id": "ord-1", "status": "resting"}})])
    client = KalshiClient(base_url="https://api.example.test", session=session, credentials=object())
    monkeypatch.setattr(client, "_build_auth_headers", lambda method, path: {"Authorization": "stub"})

    order = client.get_order("ord-1")

    assert order["order_id"] == "ord-1"
    assert session.calls[0]["url"] == "https://api.example.test/portfolio/orders/ord-1"


def test_get_orders_paginates_authenticated_list(monkeypatch):
    session = FakeSession(
        [
            FakeResponse({"orders": [{"order_id": "ord-1"}], "cursor": "NEXT"}),
            FakeResponse({"orders": [{"order_id": "ord-2"}], "cursor": None}),
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session, credentials=object())
    monkeypatch.setattr(client, "_build_auth_headers", lambda method, path: {"Authorization": "stub"})

    orders = client.get_orders(client_order_id="client-1", page_size=1, max_pages=2)

    assert [item["order_id"] for item in orders] == ["ord-1", "ord-2"]
    assert session.calls[1]["url"].endswith("/portfolio/orders?limit=1&client_order_id=client-1&cursor=NEXT")


def test_get_events_with_nested_markets_normalizes_market_prices():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "events": [
                        {
                            "event_ticker": "KXRTANIMAL",
                            "title": "Animal Farm Rotten Tomatoes",
                            "markets": [
                                {
                                    "ticker": "KXRTANIMAL-ABOVE80",
                                    "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                                    "yes_bid_dollars": "0.41",
                                    "no_bid_dollars": "0.56",
                                }
                            ],
                        }
                    ],
                    "cursor": None,
                }
            )
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session)

    events = client.get_events(status="open", with_nested_markets=True)

    assert events[0]["markets"][0]["yes_bid"] == 0.41
    assert events[0]["markets"][0]["no_bid"] == 0.56
    assert events[0]["markets"][0]["yes_ask"] == 0.44


def test_search_events_prefers_matching_event_and_nested_markets():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "events": [
                        {
                            "event_ticker": "KXRTANIMAL",
                            "title": "Animal Farm Rotten Tomatoes",
                            "markets": [
                                {"ticker": "KXRTANIMAL-ABOVE80", "title": "Will Animal Farm score above 80% on Rotten Tomatoes?"}
                            ],
                        },
                        {
                            "event_ticker": "KXOTHER",
                            "title": "Other market",
                            "markets": [],
                        },
                    ],
                    "cursor": None,
                }
            )
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session)

    results = client.search_events("Animal Farm", status="open", limit=5)

    assert results[0]["event_ticker"] == "KXRTANIMAL"


def test_get_live_market_snapshot_uses_events_fast_path():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "events": [
                        {
                            "event_ticker": "KXRTANIMAL",
                            "title": "Animal Farm Rotten Tomatoes",
                            "markets": [
                                {
                                    "ticker": "KXRTANIMAL-ABOVE80",
                                    "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                                    "floor_strike": 80,
                                    "yes_bid_dollars": "0.41",
                                    "no_bid_dollars": "0.56",
                                }
                            ],
                        }
                    ],
                    "cursor": None,
                }
            ),
            FakeResponse(
                {
                    "orderbook": {
                        "ticker": "KXRTANIMAL-ABOVE80",
                        "yes_dollars": [[41, 10]],
                        "no_dollars": [[56, 8]],
                    }
                }
            ),
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session)

    snapshot = client.get_live_market_snapshot("Animal Farm", include_orderbooks=True)

    assert snapshot["match_type"] == "event"
    assert snapshot["event"]["event_ticker"] == "KXRTANIMAL"
    assert snapshot["markets"][0]["ticker"] == "KXRTANIMAL-ABOVE80"
    assert snapshot["markets"][0]["yes_bid"] == 0.41
    assert snapshot["markets"][0]["no_bid"] == 0.56


def test_normalize_market_payload_maps_dollar_fields():
    market = normalize_market_payload(
        {
            "ticker": "KXTEST",
            "yes_bid_dollars": "0.39",
            "no_bid_dollars": "0.58",
        }
    )

    assert market["yes_bid"] == 0.39
    assert market["no_bid"] == 0.58
    assert market["yes_ask"] == 0.42
    assert market["no_ask"] == 0.61


def test_merge_market_with_orderbook_uses_best_bids():
    merged = merge_market_with_orderbook(
        {"ticker": "KXTEST", "title": "Test"},
        {
            "ticker": "KXTEST",
            "yes_dollars": [[44, 5], [43, 10]],
            "no_dollars": [[53, 6], [52, 9]],
        },
    )

    assert merged["yes_bid"] == 0.44
    assert merged["no_bid"] == 0.53
    assert merged["yes_ask"] == 0.47
    assert merged["no_ask"] == 0.56


def test_enrich_markets_with_orderbooks_merges_batch_results():
    class FakeClient:
        def get_multiple_orderbooks(self, tickers, depth=10):
            assert list(tickers) == ["KXTEST"]
            return {
                "KXTEST": {
                    "ticker": "KXTEST",
                    "yes_dollars": [[45, 12]],
                    "no_dollars": [[52, 8]],
                }
            }

    markets = enrich_markets_with_orderbooks(
        FakeClient(),
        [{"ticker": "KXTEST", "title": "Test market"}],
    )

    assert markets[0]["yes_bid"] == 0.45
    assert markets[0]["no_bid"] == 0.52


def test_fetch_live_market_snapshot_uses_client():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "events": [
                        {
                            "event_ticker": "KXRTANIMAL",
                            "title": "Animal Farm Rotten Tomatoes",
                            "markets": [],
                        }
                    ],
                    "cursor": None,
                }
            )
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session)

    snapshot = fetch_live_market_snapshot("Animal Farm", client=client, include_orderbooks=False)

    assert snapshot["match_type"] == "event"


def test_parse_kalshi_url_extracts_ticker_when_present():
    parsed = parse_kalshi_url("https://kalshi.com/markets/KXRTANIMAL-ABOVE80")

    assert parsed["ticker"] == "KXRTANIMAL-ABOVE80"


def test_fetch_live_market_snapshot_accepts_kalshi_url_with_ticker():
    session = FakeSession(
        [
            FakeResponse({"market": {"ticker": "KXRTANIMAL-ABOVE80", "title": "Will Animal Farm score above 80% on Rotten Tomatoes?"}}),
            FakeResponse({"orderbook": {"ticker": "KXRTANIMAL-ABOVE80", "yes_dollars": [[41, 10]], "no_dollars": [[56, 8]]}}),
        ]
    )
    client = KalshiClient(base_url="https://api.example.test", session=session)

    snapshot = fetch_live_market_snapshot("https://kalshi.com/markets/KXRTANIMAL-ABOVE80", client=client)

    assert snapshot["match_type"] == "ticker"
    assert snapshot["markets"][0]["ticker"] == "KXRTANIMAL-ABOVE80"

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


def _cumulative_normal(x: float, mean: float, std: float) -> float:
    """Standard normal cumulative distribution function (CDF)."""
    if std <= 0:
        return 1.0 if x >= mean else 0.0
    return 0.5 * (1.0 + math.erf((x - mean) / (std * math.sqrt(2.0))))


def estimate_contract_probability(
    market: Dict[str, Any],
    predicted_score: float,
    score_stdev: float = 5.0,
) -> Optional[float]:
    """
    Given a market contract definition and our rolling predicted Tomatometer score
    (with an assumed Gaussian uncertainty score_stdev), calculates model probability P(YES).
    """
    floor_strike = market.get("floor_strike")
    cap_strike = market.get("cap_strike")
    title = str(market.get("title") or market.get("subtitle") or "").lower()

    # Convert 0.80 -> 80.0 if strike is given as decimal fraction
    if floor_strike is not None:
        floor_strike = float(floor_strike) * 100.0 if float(floor_strike) <= 1.0 else float(floor_strike)
    if cap_strike is not None:
        cap_strike = float(cap_strike) * 100.0 if float(cap_strike) <= 1.0 else float(cap_strike)

    # Rule 1: Range market (between X and Y)
    if floor_strike is not None and cap_strike is not None:
        p_low = _cumulative_normal(float(floor_strike), predicted_score, score_stdev)
        p_high = _cumulative_normal(float(cap_strike), predicted_score, score_stdev)
        return max(0.01, min(0.99, p_high - p_low))

    # Rule 2: Above threshold / Floor strike
    if floor_strike is not None:
        p_below = _cumulative_normal(float(floor_strike), predicted_score, score_stdev)
        return max(0.01, min(0.99, 1.0 - p_below))

    # Rule 3: Below threshold / Cap strike
    if cap_strike is not None:
        p_below = _cumulative_normal(float(cap_strike), predicted_score, score_stdev)
        return max(0.01, min(0.99, p_below))

    # Rule 4: Text-based heuristics ("be Fresh", "be Rotten")
    if "fresh" in title:
        p_below_60 = _cumulative_normal(60.0, predicted_score, score_stdev)
        return max(0.01, min(0.99, 1.0 - p_below_60))
    if "rotten" in title:
        p_below_60 = _cumulative_normal(60.0, predicted_score, score_stdev)
        return max(0.01, min(0.99, p_below_60))

    return None


def score_probability_for_contract(arg1: Any, arg2: Any, arg3: Any = None) -> float:
    """
    Overloaded adapter accepting either:
      score_probability_for_contract(predicted_score, score_stdev, contract)
    or
      score_probability_for_contract(contract, predicted_score, score_stdev)
    """
    if isinstance(arg1, (int, float)) and isinstance(arg3, dict):
        prob = estimate_contract_probability(market=arg3, predicted_score=float(arg1), score_stdev=float(arg2))
    elif isinstance(arg1, dict):
        prob = estimate_contract_probability(market=arg1, predicted_score=float(arg2), score_stdev=float(arg3 or 5.0))
    else:
        prob = 0.5
    return float(prob if prob is not None else 0.5)


def plan_directional_event_orders(
    calculated_tomatometer: float,
    markets: List[Dict[str, Any]],
    score_stdev: float = 5.0,
    min_edge: float = 0.04,
    max_orders: int = 5,
    max_units_per_order: int = 5,
    price_buffer: float = 0.02,
) -> Dict[str, Any]:
    """
    Scans live event contracts and formulates limit order intents where
    our model's estimated probability diverges from the market implied probability
    by at least `min_edge`.
    """
    orders: List[Dict[str, Any]] = []

    for m in markets:
        ticker = m.get("ticker")
        if not ticker:
            continue

        model_p = estimate_contract_probability(m, calculated_tomatometer, score_stdev)
        if model_p is None:
            continue

        # Extract market prices
        yes_ask = m.get("yes_ask")
        no_ask = m.get("no_ask")

        # Convert cents to probability if necessary (e.g. 45 -> 0.45)
        if yes_ask is not None and yes_ask > 1.0:
            yes_ask = yes_ask / 100.0
        if no_ask is not None and no_ask > 1.0:
            no_ask = no_ask / 100.0

        # Check YES opportunity
        if yes_ask is not None and (model_p - yes_ask) >= min_edge:
            limit_p = min(0.99, round(yes_ask + price_buffer, 2))
            orders.append({
                "market_ticker": ticker,
                "ticker": ticker,
                "side": "yes",
                "action": "buy",
                "count": max_units_per_order,
                "limit_price": limit_p,
                "title": m.get("title") or ticker,
                "expected_edge": round(model_p - yes_ask, 4),
                "contract_type": "directional_yes",
                "model_probability_for_side": round(model_p, 4),
                "market_buy_price": yes_ask,
            })
            continue

        # Check NO opportunity
        market_p_no = (1.0 - model_p)
        if no_ask is not None and (market_p_no - no_ask) >= min_edge:
            limit_p = min(0.99, round(no_ask + price_buffer, 2))
            orders.append({
                "market_ticker": ticker,
                "ticker": ticker,
                "side": "no",
                "action": "buy",
                "count": max_units_per_order,
                "limit_price": limit_p,
                "title": m.get("title") or ticker,
                "expected_edge": round(market_p_no - no_ask, 4),
                "contract_type": "directional_no",
                "model_probability_for_side": round(market_p_no, 4),
                "market_buy_price": no_ask,
            })

    # Sort orders by highest edge descending, limit to max_orders
    orders.sort(key=lambda x: x.get("expected_edge", 0.0), reverse=True)
    orders = orders[:max_orders]

    return {
        "calculated_tomatometer": calculated_tomatometer,
        "orders": orders,
        "order_count": len(orders),
    }

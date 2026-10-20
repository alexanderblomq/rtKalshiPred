from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from settings import DEFAULT_EDGE_THRESHOLD


def _clamp_probability(value: float) -> float:
    return max(0.01, min(0.99, float(value)))


def _normal_cdf(value: float, mean: float, stddev: float) -> float:
    safe_stddev = max(stddev, 1e-6)
    z = (value - mean) / (safe_stddev * math.sqrt(2.0))
    return 0.5 * (1.0 + math.erf(z))


@dataclass(frozen=True)
class AggregateWeightingConfig:
    inclusion_probability_key: str = "rt_inclusion_probability"
    ingestion_lag_weight_key: str = "ingestion_lag_weight"
    review_weight_key: str = "aggregate_weight"
    default_inclusion_probability: float = 1.0
    default_ingestion_lag_weight: float = 1.0
    default_review_weight: float = 1.0
    prior_mean: float = 0.5
    prior_weight: float = 2.0
    confidence_rate: float = 8.0
    base_stddev: float = 0.18
    min_stddev: float = 0.04
    binary_fresh_threshold: float = 0.60


@dataclass(frozen=True)
class AggregateEstimate:
    mean_score: float
    stddev: float
    effective_review_weight: float
    counted_reviews: int
    evidence_confidence: float


def _confidence_from_evidence(effective_review_weight: float, config: AggregateWeightingConfig) -> float:
    if effective_review_weight <= 0.0:
        return 0.0
    return min(0.95, 1.0 - math.exp(-effective_review_weight / max(config.confidence_rate, 1e-6)))


def _review_effective_weight(
    review: Dict[str, Any],
    config: AggregateWeightingConfig,
) -> float:
    inclusion_probability = float(
        review.get(config.inclusion_probability_key, config.default_inclusion_probability)
    )
    lag_weight = float(review.get(config.ingestion_lag_weight_key, config.default_ingestion_lag_weight))
    explicit_weight = float(review.get(config.review_weight_key, config.default_review_weight))
    return max(0.0, inclusion_probability) * max(0.0, lag_weight) * max(0.0, explicit_weight)


def estimate_score_distribution(
    observed_reviews: List[Dict[str, Any]],
    snapshot: Optional[Dict[str, Any]] = None,
    config: Optional[AggregateWeightingConfig] = None,
) -> AggregateEstimate:
    active_config = config or AggregateWeightingConfig()
    runtime_snapshot = snapshot or {}

    weighted_fresh = active_config.prior_mean * active_config.prior_weight
    total_weight = active_config.prior_weight
    counted_reviews = 0

    for review in observed_reviews:
        if review.get("fresh_probability") is None:
            continue
        weight = _review_effective_weight(review, active_config)
        if weight <= 0.0:
            continue
        weighted_fresh += float(review["fresh_probability"]) * weight
        total_weight += weight
        counted_reviews += 1

    derived_mean = weighted_fresh / total_weight if total_weight > 0.0 else active_config.prior_mean
    snapshot_score = runtime_snapshot.get("calculated_tomatometer")
    if snapshot_score is not None:
        mean_score = float(snapshot_score) / 100.0
    else:
        mean_score = derived_mean

    stddev = max(
        active_config.min_stddev,
        active_config.base_stddev / math.sqrt(max(total_weight, 1.0)),
    )
    evidence_confidence = _confidence_from_evidence(total_weight - active_config.prior_weight, active_config)
    return AggregateEstimate(
        mean_score=max(0.0, min(1.0, mean_score)),
        stddev=stddev,
        effective_review_weight=max(total_weight - active_config.prior_weight, 0.0),
        counted_reviews=counted_reviews,
        evidence_confidence=evidence_confidence,
    )


def _probability_from_estimate(
    market: Dict[str, Any],
    estimate: AggregateEstimate,
    config: AggregateWeightingConfig,
) -> float:
    market_type = str(market.get("market_type") or "unknown")
    binary_side = str(market.get("binary_side") or "fresh")
    threshold = market.get("threshold")
    comparator = str(market.get("comparator") or "").lower()

    if market_type == "binary_fresh_rotten":
        fresh_probability = 1.0 - _normal_cdf(config.binary_fresh_threshold, estimate.mean_score, estimate.stddev)
        return _clamp_probability(fresh_probability if binary_side == "fresh" else 1.0 - fresh_probability)

    if market_type == "threshold_score" and threshold is not None:
        target = float(threshold)
        if comparator in {"above", "greater than"}:
            return _clamp_probability(1.0 - _normal_cdf(target, estimate.mean_score, estimate.stddev))
        if comparator in {"below", "at most", "less than"}:
            return _clamp_probability(_normal_cdf(target, estimate.mean_score, estimate.stddev))

    if market_type == "range_score":
        low = market.get("range_low")
        high = market.get("range_high")
        if low is None and threshold is not None:
            low = threshold
        if high is None and market.get("cap") is not None:
            high = market.get("cap")
        if low is not None and high is not None:
            lower = float(low)
            upper = float(high)
            probability = _normal_cdf(upper, estimate.mean_score, estimate.stddev) - _normal_cdf(
                lower,
                estimate.mean_score,
                estimate.stddev,
            )
            return _clamp_probability(probability)

    return _clamp_probability(estimate.mean_score)


def estimate_market_probability(
    market: Dict[str, Any],
    observed_reviews: List[Dict[str, Any]],
    snapshot: Optional[Dict[str, Any]] = None,
    config: Optional[AggregateWeightingConfig] = None,
) -> float:
    active_config = config or AggregateWeightingConfig()
    estimate = estimate_score_distribution(observed_reviews, snapshot=snapshot, config=active_config)
    return _probability_from_estimate(market, estimate, active_config)


def recommend_trade(
    market: Dict[str, Any],
    observed_reviews: List[Dict[str, Any]],
    snapshot: Optional[Dict[str, Any]] = None,
    config: Optional[AggregateWeightingConfig] = None,
) -> Dict[str, object]:
    active_config = config or AggregateWeightingConfig()
    estimate = estimate_score_distribution(observed_reviews, snapshot=snapshot, config=active_config)
    model_prob = _probability_from_estimate(market, estimate, active_config)
    market_prob = float(market.get("market_prob", 0.50))
    edge = model_prob - market_prob

    if edge >= DEFAULT_EDGE_THRESHOLD:
        recommendation = "BUY YES"
    elif edge <= -DEFAULT_EDGE_THRESHOLD:
        recommendation = "BUY NO"
    else:
        recommendation = "NO TRADE"

    return {
        "model_prob": round(model_prob, 4),
        "market_prob": round(market_prob, 4),
        "edge": round(edge, 4),
        "recommendation": recommendation,
        "estimate_mean_score": round(estimate.mean_score, 4),
        "estimate_stddev": round(estimate.stddev, 4),
        "effective_review_weight": round(estimate.effective_review_weight, 4),
        "counted_reviews": estimate.counted_reviews,
        "evidence_confidence": round(estimate.evidence_confidence, 4),
    }

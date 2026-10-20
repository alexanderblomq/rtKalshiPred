from __future__ import annotations

import numpy as np

from market.aggregate_predictor import (
    AggregateWeightingConfig,
    estimate_market_probability,
    estimate_score_distribution,
    recommend_trade,
)
from models.review_classifier import apply_probability_calibration, predict_review_freshness
from models.trainer import apply_sigmoid_calibrator, fit_sigmoid_calibrator


def test_apply_probability_calibration_sigmoid_changes_confidence() -> None:
    calibrator = {"method": "sigmoid", "coef": 0.5, "intercept": 0.0}
    calibrated = apply_probability_calibration(0.9, calibrator=calibrator)
    assert 0.5 < calibrated < 0.9


def test_predict_review_freshness_uses_calibrator_for_heuristic_path() -> None:
    review = {
        "headline": "A terrific and wonderful movie",
        "body_text": "An excellent, engaging and beautiful film.",
    }
    baseline = predict_review_freshness(review, calibrator={"method": "identity"})
    cooled = predict_review_freshness(review, calibrator={"method": "temperature", "temperature": 2.0, "bias": 0.0})
    assert 0.5 < cooled < baseline


def test_fit_sigmoid_calibrator_round_trip() -> None:
    probabilities = np.array([0.1, 0.2, 0.8, 0.9])
    labels = np.array([0, 0, 1, 1])
    calibrator = fit_sigmoid_calibrator(probabilities, labels)
    calibrated = apply_sigmoid_calibrator(probabilities, calibrator)
    assert calibrator["method"] == "sigmoid"
    assert calibrated.shape == probabilities.shape
    assert calibrated[0] < calibrated[-1]


def test_estimate_score_distribution_uses_inclusion_and_lag_weighting() -> None:
    reviews = [
        {"fresh_probability": 0.95, "rt_inclusion_probability": 1.0, "ingestion_lag_weight": 1.0},
        {"fresh_probability": 0.10, "rt_inclusion_probability": 0.1, "ingestion_lag_weight": 0.2},
    ]
    weighted = estimate_score_distribution(reviews)
    unweighted = estimate_score_distribution(
        reviews,
        config=AggregateWeightingConfig(
            inclusion_probability_key="missing_inclusion",
            ingestion_lag_weight_key="missing_lag",
            default_inclusion_probability=1.0,
            default_ingestion_lag_weight=1.0,
            prior_weight=0.0,
        ),
    )
    assert weighted.mean_score > unweighted.mean_score
    assert weighted.effective_review_weight < unweighted.effective_review_weight


def test_threshold_probability_is_parameterized_by_distribution() -> None:
    reviews = [{"fresh_probability": 0.82}, {"fresh_probability": 0.79}, {"fresh_probability": 0.84}]
    market = {"market_type": "threshold_score", "threshold": 0.80, "comparator": "above", "market_prob": 0.5}
    tight = estimate_market_probability(
        market,
        reviews,
        config=AggregateWeightingConfig(prior_weight=0.0, base_stddev=0.08, min_stddev=0.02),
    )
    diffuse = estimate_market_probability(
        market,
        reviews,
        config=AggregateWeightingConfig(prior_weight=0.0, base_stddev=0.30, min_stddev=0.20),
    )
    assert tight > diffuse
    assert 0.01 <= diffuse <= 0.99


def test_range_market_probability_works_with_explicit_bounds() -> None:
    reviews = [{"fresh_probability": 0.81}, {"fresh_probability": 0.83}, {"fresh_probability": 0.79}]
    market = {
        "market_type": "range_score",
        "range_low": 0.75,
        "range_high": 0.84,
        "market_prob": 0.4,
    }
    recommendation = recommend_trade(
        market,
        reviews,
        config=AggregateWeightingConfig(prior_weight=0.0, base_stddev=0.06, min_stddev=0.03),
    )
    assert recommendation["model_prob"] > 0.5
    assert recommendation["estimate_mean_score"] > 0.75
    assert recommendation["counted_reviews"] == 3


def test_binary_fresh_rotten_uses_configurable_fresh_threshold() -> None:
    reviews = [{"fresh_probability": 0.58}, {"fresh_probability": 0.61}, {"fresh_probability": 0.59}]
    market = {"market_type": "binary_fresh_rotten", "binary_side": "fresh"}
    default_probability = estimate_market_probability(
        market,
        reviews,
        config=AggregateWeightingConfig(prior_weight=0.0, base_stddev=0.05, min_stddev=0.03),
    )
    relaxed_probability = estimate_market_probability(
        market,
        reviews,
        config=AggregateWeightingConfig(
            prior_weight=0.0,
            base_stddev=0.05,
            min_stddev=0.03,
            binary_fresh_threshold=0.55,
        ),
    )
    assert relaxed_probability > default_probability

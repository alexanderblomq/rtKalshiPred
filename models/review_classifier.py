from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Dict, Mapping, Optional

import joblib
import pandas as pd

from scrapers.base_scraper import resolve_primary_critic_name
from scrapers.score_normalizer import normalize_score


POSITIVE_WORDS = {
    "excellent", "great", "terrific", "sharp", "funny", "moving", "strong",
    "compelling", "wonderful", "good", "engaging", "effective", "delightful",
    "smart", "thrilling", "vivid", "beautiful", "rewarding", "exalted",
}

NEGATIVE_WORDS = {
    "bad", "poor", "weak", "awful", "dull", "boring", "messy", "half-baked",
    "misguided", "tedious", "flat", "hollow", "terrible", "worst", "bland",
    "disappointing", "overlong", "lifeless", "clumsy",
}

DEFAULT_MODEL_PATH = Path("model_output/review_classifier/model.joblib")
DEFAULT_CALIBRATOR_PATH = Path("model_output/review_classifier/calibration.json")
_MODEL = None
_CALIBRATOR = None


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _clamp_probability(value: float) -> float:
    return max(1e-6, min(1.0 - 1e-6, float(value)))


def _logit(value: float) -> float:
    clipped = _clamp_probability(value)
    return math.log(clipped / (1.0 - clipped))


def _word_score(text: str) -> float:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return 0.0
    pos = sum(1 for word in words if word in POSITIVE_WORDS)
    neg = sum(1 for word in words if word in NEGATIVE_WORDS)
    return (pos - neg) / max(len(words), 20) * 20.0


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if DEFAULT_MODEL_PATH.exists():
        _MODEL = joblib.load(DEFAULT_MODEL_PATH)
    return _MODEL


def _load_calibrator() -> Optional[Mapping[str, float]]:
    global _CALIBRATOR
    if _CALIBRATOR is not None:
        return _CALIBRATOR
    if DEFAULT_CALIBRATOR_PATH.exists():
        _CALIBRATOR = json.loads(DEFAULT_CALIBRATOR_PATH.read_text(encoding="utf-8"))
    return _CALIBRATOR


def _build_model_frame(review: Dict[str, object]) -> pd.DataFrame:
    score_result = normalize_score(review.get("original_score") or review.get("raw_score"))
    combined_text = " \n ".join(
        str(value)
        for value in [
            review.get("headline") or "",
            review.get("rt_quote") or "",
            review.get("body_text") or "",
        ]
        if value
    )
    return pd.DataFrame(
        [
            {
                "combined_text": combined_text,
                "publication_id": review.get("publication_id") or "",
                "critic_name": resolve_primary_critic_name(
                    critic_name=review.get("critic_name"),
                    critic_names=review.get("critic_names"),
                ),
                "normalized_score": score_result["normalized_score"] if score_result["normalized_score"] is not None else -1.0,
            }
        ]
    )


def apply_probability_calibration(
    probability: float,
    calibrator: Optional[Mapping[str, float]] = None,
) -> float:
    active = calibrator if calibrator is not None else _load_calibrator()
    if not active:
        return _clamp_probability(probability)

    method = str(active.get("method") or "identity")
    if method == "identity":
        return _clamp_probability(probability)

    if method == "sigmoid":
        coef = float(active.get("coef", 1.0))
        intercept = float(active.get("intercept", 0.0))
        return _clamp_probability(_sigmoid((coef * _logit(probability)) + intercept))

    if method == "temperature":
        temperature = max(float(active.get("temperature", 1.0)), 1e-6)
        bias = float(active.get("bias", 0.0))
        return _clamp_probability(_sigmoid((_logit(probability) / temperature) + bias))

    return _clamp_probability(probability)


def predict_review_freshness(
    review: Dict[str, object],
    calibrator: Optional[Mapping[str, float]] = None,
) -> float:
    """Fresh/rotten classifier using trained model when available, else heuristic fallback."""
    score_result = normalize_score(review.get("original_score") or review.get("raw_score"))
    if score_result["normalized_score"] is not None:
        return _clamp_probability(float(score_result["normalized_score"]))

    model = _load_model()
    if model is not None:
        frame = _build_model_frame(review)
        raw_probability = float(model.predict_proba(frame)[0, 1])
        return apply_probability_calibration(raw_probability, calibrator=calibrator)

    text = " ".join(
        str(value)
        for value in [
            review.get("headline") or "",
            review.get("rt_quote") or "",
            review.get("body_text") or "",
        ]
        if value
    )
    raw = _word_score(text)
    return apply_probability_calibration(_sigmoid(raw), calibrator=calibrator)

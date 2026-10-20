import re
from typing import Dict, Optional


LETTER_GRADE_VALUES = {
    "a+": 1.00,
    "a": 0.97,
    "a-": 0.93,
    "b+": 0.87,
    "b": 0.83,
    "b-": 0.80,
    "c+": 0.77,
    "c": 0.73,
    "c-": 0.70,
    "d+": 0.67,
    "d": 0.63,
    "d-": 0.60,
    "f": 0.00,
}

FRESH_THRESHOLD = 0.60


def _result(raw_score: Optional[str], normalized_score: Optional[float], reason: str, confidence: float) -> Dict[str, object]:
    fresh_label = None
    if normalized_score is not None:
        fresh_label = int(normalized_score >= FRESH_THRESHOLD)

    return {
        "raw_score": raw_score,
        "normalized_score": normalized_score,
        "fresh_label": fresh_label,
        "confidence": confidence,
        "reason": reason,
    }


def _normalize_text(raw_score: str) -> str:
    text = raw_score.strip().lower()
    text = text.replace("½", ".5")
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    return " ".join(text.split())


def normalize_score(raw_score: Optional[str]) -> Dict[str, object]:
    """Convert an explicit critic score into normalized numeric and binary labels."""
    if raw_score is None:
        return _result(raw_score, None, "Missing score", 0.0)

    text = _normalize_text(raw_score)
    if not text:
        return _result(raw_score, None, "Empty score", 0.0)

    if text in {"fresh", "certified fresh", "recommended", "positive"}:
        return _result(raw_score, 1.0, "Explicit positive verdict", 0.99)
    if text in {"rotten", "not recommended", "negative"}:
        return _result(raw_score, 0.0, "Explicit negative verdict", 0.99)

    thumbs_match = re.fullmatch(r"(thumbs?\s*up|up|yes)", text)
    if thumbs_match:
        return _result(raw_score, 1.0, "Thumbs-up style verdict", 0.98)

    thumbs_down_match = re.fullmatch(r"(thumbs?\s*down|down|no)", text)
    if thumbs_down_match:
        return _result(raw_score, 0.0, "Thumbs-down style verdict", 0.98)

    percent_match = re.fullmatch(r"(\d{1,3})(?:\.\d+)?\s*%", text)
    if percent_match:
        value = min(float(percent_match.group(1)) / 100.0, 1.0)
        return _result(raw_score, value, "Percentage score", 0.98)

    out_of_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", text)
    if out_of_match:
        numerator = float(out_of_match.group(1))
        denominator = float(out_of_match.group(2))
        if denominator > 0:
            value = min(max(numerator / denominator, 0.0), 1.0)
            return _result(raw_score, value, "Fractional score", 0.98)

    x_out_of_y_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:out of)\s*(\d+(?:\.\d+)?)", text)
    if x_out_of_y_match:
        numerator = float(x_out_of_y_match.group(1))
        denominator = float(x_out_of_y_match.group(2))
        if denominator > 0:
            value = min(max(numerator / denominator, 0.0), 1.0)
            return _result(raw_score, value, "Out-of score", 0.97)

    stars_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*stars?", text)
    if stars_match:
        value = float(stars_match.group(1)) / 4.0
        value = min(max(value, 0.0), 1.0)
        return _result(raw_score, value, "Star score with implicit 4-star scale", 0.85)

    letter_match = re.fullmatch(r"([abcdf][+-]?)", text)
    if letter_match and letter_match.group(1) in LETTER_GRADE_VALUES:
        return _result(raw_score, LETTER_GRADE_VALUES[letter_match.group(1)], "Letter grade", 0.97)

    return _result(raw_score, None, "Unsupported or ambiguous score format", 0.0)

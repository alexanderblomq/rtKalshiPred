import re
from typing import Dict, Optional


def _clean_input(market_input: str) -> str:
    text = market_input.strip()
    text = text.replace("%25", "%")
    return " ".join(text.split())


def _extract_title(text: str) -> str:
    patterns = [
        r"will\s+(.+?)\s+be\s+(?:fresh|rotten)\s+on\s+rotten\s+tomatoes",
        r"will\s+(.+?)\s+score\s+(?:above|over|below|under|at least|at most)\s+\d+(?:\.\d+)?%?\s+on\s+rotten\s+tomatoes",
        r"will\s+(.+?)\s+have\s+an?\s+rotten\s+tomatoes\s+score",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" \"'")

    return text.strip(" ?")


def _extract_threshold(text: str) -> Optional[float]:
    match = re.search(r"(above|over|below|under|at least|at most)\s+(\d+(?:\.\d+)?)\s*%?", text, flags=re.IGNORECASE)
    if not match:
        return None
    return float(match.group(2)) / 100.0


def _extract_comparator(text: str) -> Optional[str]:
    match = re.search(r"\b(above|over|below|under|at least|at most)\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    comparator = match.group(1).lower()
    if comparator == "over":
        return "above"
    if comparator == "under":
        return "below"
    return comparator


def _extract_binary_side(text: str) -> Optional[str]:
    match = re.search(r"\bbe\s+(fresh|rotten)\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower()


def _market_type(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\bbe\s+(fresh|rotten)\b", lowered):
        return "binary_fresh_rotten"
    if re.search(r"\b(above|over|below|under|at least|at most)\b", lowered):
        return "threshold_score"
    return "unknown"


def resolve_market(market_input: str) -> Dict[str, object]:
    """Resolve a Kalshi market string into an internal title/threshold object."""
    cleaned = _clean_input(market_input)
    market_type = _market_type(cleaned)

    return {
        "raw_input": market_input,
        "normalized_input": cleaned,
        "title": _extract_title(cleaned),
        "title_type": "movie",
        "market_type": market_type,
        "binary_side": _extract_binary_side(cleaned),
        "threshold": _extract_threshold(cleaned),
        "comparator": _extract_comparator(cleaned),
    }

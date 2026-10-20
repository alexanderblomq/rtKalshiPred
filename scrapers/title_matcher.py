import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional


STOP_WORDS = {"the", "a", "an"}


def _extract_year(text: str) -> Optional[int]:
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        return int(match.group(0))
    return None


def _normalize_title(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\((19|20)\d{2}\)", " ", text)
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w\s]|_", " ", text, flags=re.UNICODE)
    tokens = [token for token in text.split() if token not in STOP_WORDS]
    return " ".join(tokens)


def _score_match(candidate: str, option: str) -> float:
    normalized_candidate = _normalize_title(candidate)
    normalized_option = _normalize_title(option)

    if not normalized_candidate or not normalized_option:
        return 0.0

    candidate_year = _extract_year(candidate)
    option_year = _extract_year(option)
    if candidate_year and option_year and candidate_year != option_year:
        return 0.0

    if len(normalized_candidate) <= 3 and normalized_candidate not in normalized_option.split():
        return 0.0

    if normalized_candidate == normalized_option:
        base_score = 1.0
    elif f" {normalized_candidate} " in f" {normalized_option} " or f" {normalized_option} " in f" {normalized_candidate} ":
        base_score = 0.93
    else:
        base_score = SequenceMatcher(None, normalized_candidate, normalized_option).ratio()

    if candidate_year and option_year:
        if candidate_year == option_year:
            base_score += 0.04

    return max(0.0, min(base_score, 1.0))


def match_title(candidate: str, options: List[str]) -> Dict[str, object]:
    """Return the best candidate title match."""
    if not options:
        return {"match": None, "confidence": 0.0, "normalized_candidate": _normalize_title(candidate)}

    best_option = None
    best_score = -1.0
    for option in options:
        score = _score_match(candidate, option)
        if score > best_score:
            best_score = score
            best_option = option

    return {
        "match": best_option,
        "confidence": round(best_score, 4),
        "normalized_candidate": _normalize_title(candidate),
    }

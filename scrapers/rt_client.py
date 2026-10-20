from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from title_matcher import match_title


RT_BASE_URL = "https://www.rottentomatoes.com"
USER_AGENT = "rtKalshiPred/0.1"
MIN_TITLE_MATCH_CONFIDENCE = 0.85
MIN_TITLE_MATCH_MARGIN = 0.03


def fetch_rt_reviews(title_id: str) -> list[Dict[str, Any]]:
    """Legacy placeholder kept for compatibility."""
    return []


def fetch_rt_title_baseline(title: str, rt_title_path: Optional[str] = None) -> Dict[str, Any]:
    normalized_path = _normalize_rt_title_path(rt_title_path)
    diagnostics: Dict[str, Any] = {
        "used_explicit_path": bool(normalized_path),
        "resolution_status": "explicit_path" if normalized_path else "search_required",
        "resolution_confidence": None,
        "fetch_status": None,
        "parse_status": None,
        "message": None,
    }
    try:
        resolution = {"path": normalized_path, "confidence": None, "reason": None}
        if normalized_path:
            resolved_path = normalized_path
        else:
            resolution = _resolve_rt_title_match(title)
            diagnostics["resolution_confidence"] = resolution["confidence"]
            resolved_path = resolution["path"]
    except URLError as exc:
        return {
            "available": False,
            "target_title": title,
            "rt_title_path": normalized_path,
            "review_count": None,
            "tomatometer": None,
            "diagnostics": {
                **diagnostics,
                "resolution_status": "failed",
                "fetch_status": "failed",
                "message": f"Title resolution failed: {exc.reason}",
            },
        }
    except Exception as exc:
        return {
            "available": False,
            "target_title": title,
            "rt_title_path": normalized_path,
            "review_count": None,
            "tomatometer": None,
            "diagnostics": {
                **diagnostics,
                "resolution_status": "failed",
                "fetch_status": "failed",
                "message": f"Title resolution failed: {exc}",
            },
        }
    if not resolved_path:
        return {
            "available": False,
            "target_title": title,
            "rt_title_path": None,
            "review_count": None,
            "tomatometer": None,
            "diagnostics": {
                **diagnostics,
                "resolution_status": "not_found",
                "message": resolution["reason"] or "Could not resolve a Rotten Tomatoes movie path for this title.",
            },
        }

    try:
        html = _fetch_text(f"{RT_BASE_URL}/{resolved_path}")
        diagnostics["fetch_status"] = "ok"
    except URLError as exc:
        return {
            "available": False,
            "target_title": title,
            "rt_title_path": resolved_path,
            "rt_page_url": f"{RT_BASE_URL}/{resolved_path}",
            "review_count": None,
            "tomatometer": None,
            "diagnostics": {
                **diagnostics,
                "fetch_status": "failed",
                "message": f"Fetch failed: {exc.reason}",
            },
        }
    except Exception as exc:
        return {
            "available": False,
            "target_title": title,
            "rt_title_path": resolved_path,
            "rt_page_url": f"{RT_BASE_URL}/{resolved_path}",
            "review_count": None,
            "tomatometer": None,
            "diagnostics": {
                **diagnostics,
                "fetch_status": "failed",
                "message": f"Fetch failed: {exc}",
            },
        }

    baseline = _parse_rt_movie_page(html)
    diagnostics["parse_status"] = "ok" if baseline.get("review_count") is not None or baseline.get("tomatometer") is not None else "empty"
    baseline.update(
        {
            "available": baseline.get("review_count") is not None or baseline.get("tomatometer") is not None,
            "target_title": title,
            "rt_title_path": resolved_path,
            "rt_page_url": f"{RT_BASE_URL}/{resolved_path}",
            "diagnostics": {
                **diagnostics,
                "message": None if diagnostics["parse_status"] == "ok" else "Fetched page but could not parse review count or Tomatometer.",
            },
        }
    )
    return baseline


def _normalize_rt_title_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    normalized = path.strip().lstrip("/")
    if normalized.startswith("https://"):
        normalized = normalized.removeprefix(f"{RT_BASE_URL}/")
    return normalized or None


def _resolve_rt_title_path(title: str) -> Optional[str]:
    return _resolve_rt_title_match(title)["path"]


def _resolve_rt_title_match(title: str) -> Dict[str, Any]:
    search_url = f"{RT_BASE_URL}/search?search={quote_plus(title)}"
    html = _fetch_text(search_url)
    candidates = []
    seen_paths = set()
    for match in re.finditer(r'href="(/m/[^"#?]+)"', html):
        path = match.group(1).lstrip("/")
        if path in seen_paths:
            continue
        seen_paths.add(path)
        candidates.append(path)
    if not candidates:
        return {"path": None, "confidence": None, "reason": "Could not resolve a Rotten Tomatoes movie path for this title."}

    scored_candidates = []
    for path in candidates:
        option = path.split("/")[-1].replace("_", " ")
        score = float(match_title(title, [option])["confidence"])
        scored_candidates.append((path, score))

    scored_candidates.sort(key=lambda item: item[1], reverse=True)
    best_path, best_score = scored_candidates[0]
    second_score = scored_candidates[1][1] if len(scored_candidates) > 1 else None

    if best_score < MIN_TITLE_MATCH_CONFIDENCE:
        return {
            "path": None,
            "confidence": best_score,
            "reason": f"Could not confidently resolve a Rotten Tomatoes movie path for '{title}'.",
        }
    if second_score is not None and (best_score - second_score) < MIN_TITLE_MATCH_MARGIN:
        return {
            "path": None,
            "confidence": best_score,
            "reason": f"Rotten Tomatoes title search for '{title}' was ambiguous.",
        }
    return {"path": best_path, "confidence": best_score, "reason": None}


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def _parse_rt_movie_page(html: str) -> Dict[str, Any]:
    payload = _extract_ld_json(html)
    aggregate = payload.get("aggregateRating") if isinstance(payload, dict) else {}

    review_count = _parse_review_count(html, aggregate if isinstance(aggregate, dict) else {})
    tomatometer = _parse_tomatometer(html, aggregate if isinstance(aggregate, dict) else {})

    return {
        "review_count": review_count,
        "tomatometer": tomatometer,
    }


def _extract_ld_json(html: str) -> Dict[str, Any]:
    match = re.search(
        r'<script[^>]+type="application/ld\+json"[^>]*>\s*(\{.*?\})\s*</script>',
        html,
        re.S,
    )
    if not match:
        return {}
    try:
        payload = json.loads(match.group(1))
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        return {}
    return {}


def _parse_review_count(html: str, aggregate: Dict[str, Any]) -> Optional[int]:
    if isinstance(aggregate.get("reviewCount"), int):
        return int(aggregate["reviewCount"])
    if isinstance(aggregate.get("reviewCount"), str) and aggregate["reviewCount"].isdigit():
        return int(aggregate["reviewCount"])

    match = re.search(r"Tomatometer\s+(\d+)\s+Reviews", html, re.I)
    if match:
        return int(match.group(1))
    return None


def _parse_tomatometer(html: str, aggregate: Dict[str, Any]) -> Optional[float]:
    rating = aggregate.get("ratingValue")
    if isinstance(rating, (int, float)):
        return float(rating)
    if isinstance(rating, str):
        try:
            return float(rating)
        except ValueError:
            pass

    match = re.search(r"(\d+)%\s+Tomatometer", html, re.I)
    if match:
        return float(match.group(1))
    return None

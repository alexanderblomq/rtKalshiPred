from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional, Sequence
from urllib.parse import urlparse

from review_candidate_filter import classify_review_candidate
from scrapers.base_scraper import PublicationConfig, SourceRule
from title_matcher import match_title
from utils.review_url_filters import looks_like_article_url


TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "for",
    "from",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}


def is_allowed_review_url(rule: SourceRule, url: str) -> bool:
    if not looks_like_article_url(url):
        return False
    if rule.allowed_url_prefixes and not any(url.startswith(prefix) for prefix in rule.allowed_url_prefixes):
        return False
    if rule.review_url_keywords and not any(keyword.lower() in url.lower() for keyword in rule.review_url_keywords):
        return False
    return True


def process_url_candidate(
    scraper: Any,
    title: str,
    url: str,
    min_review_likeness: float,
    extra_fields: Optional[Mapping[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    try:
        record = scraper.scrape(url)
    except Exception:
        return None

    review_meta = classify_review_candidate(record)
    if review_meta["review_likeness"] < min_review_likeness:
        return None

    candidate_options = [
        value
        for value in [
            record.get("headline"),
            record.get("canonical_url"),
            record.get("source_url"),
        ]
        if value
    ]
    match = match_title(title, candidate_options)

    candidate = {
        "publication_id": scraper.publication.publication_id,
        "outlet_name": scraper.publication.outlet_name,
        "url": record.get("canonical_url") or record.get("source_url"),
        "headline": record.get("headline"),
        "published_at": record.get("published_at"),
        "raw_score": record.get("raw_score"),
        "match_confidence": float(match["confidence"]),
        "candidate_title": match.get("match"),
        "review_likeness": review_meta["review_likeness"],
    }
    if extra_fields:
        candidate.update(extra_fields)
    return candidate


def review_candidate_sort_key(item: Mapping[str, Any]) -> tuple:
    return (
        -float(item.get("match_confidence", 0.0)),
        -float(item.get("review_likeness", 0.0)),
        str(item.get("publication_id") or ""),
        str(item.get("url") or ""),
        str(item.get("headline") or ""),
        str(item.get("published_at") or ""),
    )


def extract_title_tokens(title: str) -> list[str]:
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", (title or "").lower())
        if len(token) >= 3 and token not in TITLE_STOPWORDS
    ]
    return list(dict.fromkeys(tokens))


def score_url_for_title(url: str, title: str) -> float:
    if not url or not title:
        return 0.0
    parsed = urlparse(url)
    normalized = f"{parsed.netloc}{parsed.path}".lower()
    tokens = extract_title_tokens(title)
    if not tokens:
        return 0.0

    score = 0.0
    matched = 0
    for token in tokens:
        if token in normalized:
            matched += 1
            score += 1.5
            if re.search(rf"(?:^|[-_/]){re.escape(token)}(?:$|[-_/])", normalized):
                score += 1.0
    if matched:
        score += matched / max(len(tokens), 1)
        phrase = "-".join(tokens)
        if phrase and phrase in normalized:
            score += 3.0
    return score


def score_review_url(
    url: str,
    rule: Optional[SourceRule] = None,
    publication: Optional[PublicationConfig] = None,
    title: Optional[str] = None,
) -> float:
    if not url:
        return float("-inf")
    score = 0.0
    lowered = url.lower()
    parsed = urlparse(lowered)
    path = parsed.path or ""
    segments = [segment for segment in path.split("/") if segment]

    if looks_like_article_url(url):
        score += 2.0
    if rule is not None:
        if rule.allowed_url_prefixes and any(url.startswith(prefix) for prefix in rule.allowed_url_prefixes):
            score += 2.0
        if rule.review_url_keywords:
            score += min(sum(1 for keyword in rule.review_url_keywords if keyword and keyword.lower() in lowered), 3) * 1.2
        if rule.generated is False:
            score += 0.5
    if publication is not None:
        inferred_review_path_prefix = getattr(publication, "inferred_review_path_prefix", None)
        review_url_count = getattr(publication, "review_url_count", None)
        if inferred_review_path_prefix and str(inferred_review_path_prefix).lower() in lowered:
            score += 1.5
        if review_url_count:
            score += min(float(review_url_count) / 100.0, 2.0)
    if len(segments) >= 3:
        score += 1.0
    if len(segments) >= 5:
        score += 0.5
    if re.search(r"/20\d{2}/", path):
        score += 0.8
    if any(keyword in lowered for keyword in ("/review", "-review", "review-", "/reviews/")):
        score += 1.0
    if parsed.query:
        score -= 0.5
    if title:
        score += score_url_for_title(url, title)
    return score


def prioritize_candidate_urls(
    urls: Sequence[str],
    *,
    rule: Optional[SourceRule] = None,
    publication: Optional[PublicationConfig] = None,
    title: Optional[str] = None,
    limit: Optional[int] = None,
    require_title_match: bool = False,
) -> list[str]:
    deduped = list(dict.fromkeys(url for url in urls if url))
    if not deduped:
        return []

    scored: list[tuple[float, float, str]] = []
    has_title_match = False
    for url in deduped:
        title_score = score_url_for_title(url, title or "")
        if title_score > 0.0:
            has_title_match = True
        total_score = score_review_url(url, rule=rule, publication=publication, title=title)
        scored.append((title_score, total_score, url))

    if require_title_match and has_title_match:
        scored = [item for item in scored if item[0] > 0.0]

    scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
    prioritized = [url for _, _, url in scored]
    if limit is not None:
        prioritized = prioritized[:limit]
    return prioritized


def publication_priority_key(publication: PublicationConfig, rule: Optional[SourceRule] = None) -> tuple:
    return (
        0 if getattr(publication, "enabled", True) else 1,
        0 if getattr(publication, "approved_publication", False) else 1,
        0 if rule and rule.generated is False else 1,
        -int(getattr(publication, "review_url_count", 0) or 0),
        0 if getattr(publication, "site_base_url", None) else 1,
        str(getattr(publication, "publication_id", "")),
    )

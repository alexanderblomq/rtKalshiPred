from __future__ import annotations

import re
from urllib.parse import urlparse

EXCLUDED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".mp4", ".mp3", ".wav", ".avi", ".mov",
    ".css", ".js", ".json", ".xml", ".pdf", ".zip",
}

NON_ARTICLE_PATHS = {
    "tag", "category", "author", "topics", "search",
    "privacy-policy", "terms-of-service", "about", "contact",
    "login", "register", "subscribe", "feed", "rss",
}


def looks_like_article_url(url: str) -> bool:
    """
    Heuristic check to determine if a URL points to an individual article or review
    rather than an index, category, media file, or homepage.
    """
    if not url or not isinstance(url, str):
        return False

    parsed = urlparse(url.lower().strip())
    if parsed.scheme not in ("http", "https"):
        return False

    path = parsed.path.rstrip("/")
    if not path or path == "":
        return False

    # Check for excluded file extensions
    if any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        return False

    segments = [s for s in path.split("/") if s]
    if not segments:
        return False

    # Check if the URL is just a top-level category or author page
    if len(segments) == 1 and segments[0] in NON_ARTICLE_PATHS:
        return False

    if any(seg in NON_ARTICLE_PATHS for seg in segments[:-1]) and len(segments) < 2:
        return False

    # Individual review/article URLs typically have a hyphenated slug or date structure
    last_segment = segments[-1]
    if "-" in last_segment or "_" in last_segment or len(last_segment) > 15:
        return True

    # If it has multiple path levels, it's likely an article or review subpage
    if len(segments) >= 2:
        return True

    return True

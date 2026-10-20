from __future__ import annotations

import json
import re
from pathlib import Path


PROFILE_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def _load_profile(profile_dir: Path, publication_id: str) -> dict:
    text = (profile_dir / f"{publication_id}.md").read_text(encoding="utf-8")
    match = PROFILE_BLOCK_RE.search(text)
    assert match, f"Missing JSON block for {publication_id}"
    return json.loads(match.group(1))


def _load_rule(rules_path: Path, publication_id: str) -> dict:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    for rule in rules:
        if rule["publication_id"] == publication_id:
            return rule
    raise AssertionError(f"Missing compiled rule for {publication_id}")


def test_high_value_profiles_exist_with_tightened_discovery_rules():
    repo_root = Path(__file__).resolve().parents[1]
    profile_dir = repo_root / "data" / "critic_parser_profiles"

    expected = {
        "review_film_review": {
            "discovery_url": "https://reviewfilmreview.wordpress.com",
            "allowed_prefix": "https://reviewfilmreview.wordpress.com/20",
            "keyword": "/20",
        },
        "australian_book_review": {
            "discovery_url": "https://www.australianbookreview.com.au/arts-update",
            "allowed_prefix": "https://www.australianbookreview.com.au/arts-update/",
            "keyword": "/arts-update/",
        },
        "rachelsreviews_net": {
            "discovery_url": "https://rachelsreviews.net",
            "allowed_prefix": "https://rachelsreviews.net/20",
            "keyword": "/20",
        },
        "always_good_movies": {
            "discovery_url": "https://alwaysgoodmovies.com/reviews",
            "allowed_prefix": "https://alwaysgoodmovies.com/reviews/",
            "keyword": "/reviews/",
        },
        "ripple_effects": {
            "discovery_url": "https://rippleeffects.reviews/movies-reviewed/",
            "allowed_prefix": "https://rippleeffects.reviews/20",
            "keyword": "/20",
        },
        "empire_magazine": {
            "discovery_url": "https://www.empireonline.com/movies/reviews/",
            "allowed_prefix": "https://www.empireonline.com/movies/reviews/",
            "keyword": "/movies/reviews/",
        },
        "pajiba": {
            "discovery_url": "https://www.pajiba.com/film_reviews/",
            "allowed_prefix": "https://www.pajiba.com/film_reviews/",
            "keyword": "/film_reviews/review-",
        },
        "411mania": {
            "discovery_url": "https://411mania.com/movies/",
            "allowed_prefix": "https://411mania.com/movies/",
            "keyword": "-review/",
        },
    }

    for publication_id, config in expected.items():
        profile = _load_profile(profile_dir, publication_id)
        assert profile["discovery_url"] == config["discovery_url"]
        assert config["allowed_prefix"] in profile["allowed_url_prefixes"]
        assert config["keyword"] in profile["review_url_keywords"]


def test_high_value_profiles_define_specific_selectors():
    repo_root = Path(__file__).resolve().parents[1]
    profile_dir = repo_root / "data" / "critic_parser_profiles"

    rachelsreviews = _load_profile(profile_dir, "rachelsreviews_net")
    assert rachelsreviews["selectors"]["headline_selectors"][0] == "meta[property='og:title']::attr(content)"

    empire = _load_profile(profile_dir, "empire_magazine")
    assert "h1[class*='title_h1']" in empire["selectors"]["headline_selectors"]
    assert "div[class*='ratings_review-rating']" in empire["selectors"]["score_selectors"]

    four11 = _load_profile(profile_dir, "411mania")
    assert "div[class*='scores__overview-number--'] span" in four11["selectors"]["score_selectors"]


def test_compiled_source_rules_reflect_high_value_profiles():
    repo_root = Path(__file__).resolve().parents[1]
    rules_path = repo_root / "data" / "critics" / "source_rules.json"

    review_film_review = _load_rule(rules_path, "review_film_review")
    assert review_film_review["allowed_url_prefixes"] == ["https://reviewfilmreview.wordpress.com/20"]
    assert review_film_review["review_url_keywords"] == ["/20"]

    pajiba = _load_rule(rules_path, "pajiba")
    assert pajiba["discovery_url"] == "https://www.pajiba.com/film_reviews/"
    assert pajiba["allowed_url_prefixes"] == ["https://www.pajiba.com/film_reviews/"]
    assert pajiba["review_url_keywords"] == ["/film_reviews/review-"]

    four11 = _load_rule(rules_path, "411mania")
    assert four11["score_selectors"] == [
        "div[class*='scores__overview-number--'] span",
        "div.scores__overview--number span",
    ]
    assert four11["generation_method"] == "parser-profile-v1"

from pipelines.build_source_rules import (
    build_candidate_rule,
    infer_adapter,
    infer_source_type,
    merge_rules,
)


def test_infer_source_type_youtube():
    publication = {"outlet_name": "3C Films (YouTube)", "site_base_url": None}
    assert infer_source_type(publication) == "youtube"
    assert infer_adapter(publication) == "unsupported"


def test_infer_source_type_substack():
    publication = {"outlet_name": "Auteurist Class (Substack)", "site_base_url": None}
    assert infer_source_type(publication) == "substack"
    assert infer_adapter(publication) == "article"


def test_infer_source_type_respects_existing_config():
    publication = {
        "outlet_name": "Example Publication",
        "site_base_url": "https://example.com",
        "source_type": "podcast",
        "adapter": "rss",
    }
    assert infer_source_type(publication) == "podcast"
    assert infer_adapter(publication) == "rss"


def test_build_candidate_rule_for_plain_article_publication():
    publication = {
        "publication_id": "example_pub",
        "outlet_name": "Example Publication",
        "site_base_url": "https://example.com",
    }
    rule = build_candidate_rule(publication)
    assert rule["adapter"] == "article"
    assert rule["discovery_url"] == "https://example.com"
    assert rule["generated"] is True
    assert "review" in rule["review_url_keywords"]


def test_merge_rules_preserves_existing_manual_rule():
    publications = [
        {
            "publication_id": "newyorker",
            "outlet_name": "The New Yorker",
            "site_base_url": "https://www.newyorker.com",
        },
        {
            "publication_id": "example_pub",
            "outlet_name": "Example Publication",
            "site_base_url": None,
        },
    ]
    existing_rules = [
        {
            "publication_id": "newyorker",
            "adapter": "article",
            "source_type": "article",
            "discovery_url": "https://www.newyorker.com/culture/the-front-row",
            "allowed_url_prefixes": ["https://www.newyorker.com/culture/the-front-row/"],
            "review_url_keywords": ["/culture/the-front-row/"],
            "headline_selectors": [],
            "published_at_selectors": [],
            "body_selectors": [],
            "score_selectors": [],
            "canonical_url_selectors": [],
        }
    ]

    merged = merge_rules(publications, existing_rules)
    merged_by_id = {rule["publication_id"]: rule for rule in merged}

    assert merged_by_id["newyorker"]["discovery_url"] == "https://www.newyorker.com/culture/the-front-row"
    assert merged_by_id["example_pub"]["generated"] is True

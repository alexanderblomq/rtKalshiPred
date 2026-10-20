from pipelines.enrich_publications import (
    extract_publication_review_urls,
    extract_effective_url,
    enrich_publications,
    infer_enrichment,
    infer_path_prefix,
    infer_publication_source_type,
    merge_enriched_subset,
    publication_value_score,
    select_publications,
    sort_publications_by_value,
)


def test_extract_publication_review_urls_deduplicates():
    html = """
    {"publicationReviewUrl":"https://example.com/reviews/a"}
    {"publicationReviewUrl":"https://example.com/reviews/a"}
    {"publicationReviewUrl":"https://example.com/reviews/b"}
    """
    urls = extract_publication_review_urls(html)
    assert urls == [
        "https://example.com/reviews/a",
        "https://example.com/reviews/b",
    ]


def test_infer_path_prefix_for_shared_review_path():
    prefix = infer_path_prefix(
        [
            "https://example.com/reviews/a",
            "https://example.com/reviews/b",
            "https://example.com/reviews/c",
        ]
    )
    assert prefix == "/reviews/"


def test_infer_enrichment_picks_dominant_host_and_base_url():
    enrichment = infer_enrichment(
        [
            "https://www.aarp.org/entertainment/television/a.html",
            "https://www.aarp.org/entertainment/television/b.html",
            "https://other.example.com/x",
        ]
    )
    assert enrichment["site_base_url"] == "https://www.aarp.org"
    assert enrichment["dominant_host"] == "www.aarp.org"
    assert enrichment["inferred_review_path_prefix"] == "/entertainment/television/"


def test_extract_effective_url_from_web_archive():
    archived = "https://web.archive.org/web/20020126184809/http://www.laweekly.com/ink/01/04/film-taylor.shtml"
    assert extract_effective_url(archived) == "http://www.laweekly.com/ink/01/04/film-taylor.shtml"


def test_select_publications_by_id_and_limit():
    publications = [
        {"publication_id": "a"},
        {"publication_id": "b"},
        {"publication_id": "c"},
    ]
    selected = select_publications(publications, publication_ids=["b", "c"], limit=1)
    assert selected == [{"publication_id": "b"}]


def test_merge_enriched_subset_only_updates_targeted_publications():
    publications = [
        {"publication_id": "a", "site_base_url": None},
        {"publication_id": "b", "site_base_url": None},
    ]
    enriched_subset = [
        {"publication_id": "b", "site_base_url": "https://example.com"},
    ]
    merged = merge_enriched_subset(publications, enriched_subset)
    assert merged[0]["site_base_url"] is None
    assert merged[1]["site_base_url"] == "https://example.com"


def test_infer_publication_source_type():
    assert infer_publication_source_type({"outlet_name": "Example (YouTube)"}) == "youtube"
    assert infer_publication_source_type({"outlet_name": "Example Podcast"}) == "podcast"
    assert infer_publication_source_type({"outlet_name": "Example", "site_base_url": "https://x.substack.com"}) == "substack"
    assert infer_publication_source_type({"outlet_name": "Example"}) == "article"


def test_infer_publication_source_type_respects_existing_config():
    assert infer_publication_source_type({"outlet_name": "Example", "source_type": "podcast"}) == "podcast"


def test_sort_publications_by_value_prioritizes_unresolved_approved_article_with_more_critics():
    publications = [
        {
            "publication_id": "low",
            "outlet_name": "Low",
            "approved_publication": False,
            "critic_names": [],
            "site_base_url": None,
        },
        {
            "publication_id": "high",
            "outlet_name": "High",
            "approved_publication": True,
            "critic_names": ["A", "B", "C"],
            "site_base_url": None,
        },
        {
            "publication_id": "resolved",
            "outlet_name": "Resolved",
            "approved_publication": True,
            "critic_names": ["A", "B", "C", "D"],
            "site_base_url": "https://example.com",
        },
    ]
    ordered = sort_publications_by_value(publications)
    assert ordered[0]["publication_id"] == "high"
    assert ordered[-1]["publication_id"] == "low" or ordered[-1]["publication_id"] == "resolved"


def test_select_publications_value_order_and_missing_base_url():
    publications = [
        {
            "publication_id": "resolved",
            "outlet_name": "Resolved",
            "approved_publication": True,
            "critic_names": ["A", "B"],
            "site_base_url": "https://example.com",
        },
        {
            "publication_id": "best",
            "outlet_name": "Best",
            "approved_publication": True,
            "critic_names": ["A", "B", "C"],
            "site_base_url": None,
        },
        {
            "publication_id": "worse",
            "outlet_name": "Worse",
            "approved_publication": False,
            "critic_names": [],
            "site_base_url": None,
        },
    ]
    selected = select_publications(publications, value_order=True, only_missing_base_url=True, limit=1)
    assert selected == [publications[1]]


def test_enrich_publications_records_failures(monkeypatch):
    def raise_fetch_error(publication):
        raise RuntimeError(f"failed for {publication['publication_id']}")

    monkeypatch.setattr("pipelines.enrich_publications.enrich_publication", raise_fetch_error)

    enriched, enriched_count = enrich_publications([{"publication_id": "broken", "site_base_url": None}], max_workers=1)

    assert enriched_count == 0
    assert enriched[0]["publication_id"] == "broken"
    assert enriched[0]["enrichment_error"] == "RuntimeError: failed for broken"

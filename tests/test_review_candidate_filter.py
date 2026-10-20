from scrapers.review_candidate_filter import classify_review_candidate


def test_review_candidate_filter_prefers_review_pages():
    review_record = {
        "headline": "The Drama Review",
        "source_url": "https://example.com/movies/the-drama-review/",
        "canonical_url": "https://example.com/movies/the-drama-review/",
        "body_text": "This review examines the film in depth and discusses performances, direction, and pacing." * 10,
        "raw_score": None,
    }
    newsletter_record = {
        "headline": "ISSUE #119",
        "source_url": "https://example.com/p/issue-119",
        "canonical_url": "https://example.com/p/issue-119",
        "body_text": "Welcome back to our newsletter. Tonight we are unveiling our latest programming slate." * 8,
        "raw_score": None,
    }

    review_meta = classify_review_candidate(review_record)
    newsletter_meta = classify_review_candidate(newsletter_record)

    assert review_meta["review_likeness"] > newsletter_meta["review_likeness"]
    assert review_meta["is_likely_review"] is True
    assert newsletter_meta["is_likely_review"] is False

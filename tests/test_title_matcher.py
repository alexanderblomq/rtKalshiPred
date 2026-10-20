from title_matcher import match_title


def test_match_title_prefers_exact_normalized_match():
    result = match_title("superman", ["Superman", "Batman"])
    assert result["match"] == "Superman"
    assert result["confidence"] >= 0.99


def test_match_title_handles_year_disambiguation():
    result = match_title("Suspiria (2018)", ["Suspiria (1977)", "Suspiria (2018)"])
    assert result["match"] == "Suspiria (2018)"
    assert result["confidence"] > 0.9


def test_match_title_ignores_articles_and_punctuation():
    result = match_title("The Fantastic Four: First Steps", ["Fantastic Four First Steps", "Superman"])
    assert result["match"] == "Fantastic Four First Steps"

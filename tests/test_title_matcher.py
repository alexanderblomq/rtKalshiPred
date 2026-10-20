from scrapers.title_matcher import match_title


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


def test_short_title_is_not_a_substring_of_another_word():
    assert match_title("It", ["Little Women review"])["confidence"] == 0.0
    assert match_title("It", ["It movie review"])["confidence"] > 0.9


def test_conflicting_remake_years_are_rejected():
    assert match_title("Suspiria (2018)", ["Suspiria (1977) review"])["confidence"] == 0.0


def test_numeric_and_unicode_titles_are_preserved():
    assert match_title("1917", ["1917 movie review"])["confidence"] > 0.9
    assert match_title("Amélie", ["Amélie review"])["confidence"] > 0.9

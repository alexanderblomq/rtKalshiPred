from score_normalizer import normalize_score


def test_normalize_fraction_score():
    result = normalize_score("3/4")
    assert result["normalized_score"] == 0.75
    assert result["fresh_label"] == 1


def test_normalize_letter_grade():
    result = normalize_score("B+")
    assert result["normalized_score"] == 0.87
    assert result["fresh_label"] == 1


def test_normalize_rotten_text_score():
    result = normalize_score("rotten")
    assert result["normalized_score"] == 0.0
    assert result["fresh_label"] == 0


def test_unsupported_score_is_none():
    result = normalize_score("mixed-to-positive")
    assert result["normalized_score"] is None
    assert result["fresh_label"] is None

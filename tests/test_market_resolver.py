from market.market_resolver import resolve_market


def test_resolve_market_binary_fresh():
    result = resolve_market("Will Superman be Fresh on Rotten Tomatoes?")
    assert result["title_type"] == "movie"
    assert result["title"] == "Superman"
    assert result["market_type"] == "binary_fresh_rotten"
    assert result["binary_side"] == "fresh"
    assert result["threshold"] is None
    assert result["comparator"] is None


def test_resolve_market_binary_rotten_preserves_side():
    result = resolve_market("Will Snow White be Rotten on Rotten Tomatoes?")
    assert result["title"] == "Snow White"
    assert result["market_type"] == "binary_fresh_rotten"
    assert result["binary_side"] == "rotten"
    assert result["threshold"] is None
    assert result["comparator"] is None


def test_resolve_market_threshold_above():
    result = resolve_market("Will Fantastic Four score above 80% on Rotten Tomatoes?")
    assert result["title"] == "Fantastic Four"
    assert result["market_type"] == "threshold_score"
    assert result["binary_side"] is None
    assert result["threshold"] == 0.8
    assert result["comparator"] == "above"


def test_resolve_market_threshold_under_alias():
    result = resolve_market("Will Mickey 17 score under 75 on Rotten Tomatoes?")
    assert result["title"] == "Mickey 17"
    assert result["binary_side"] is None
    assert result["threshold"] == 0.75
    assert result["comparator"] == "below"

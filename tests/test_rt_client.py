from scrapers.rt_client import _parse_rt_movie_page, _resolve_rt_title_match, fetch_rt_title_baseline


def test_parse_rt_movie_page_extracts_review_count_and_tomatometer():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Movie",
            "aggregateRating": {
              "@type": "AggregateRating",
              "ratingValue": 73,
              "reviewCount": 5
            }
          }
        </script>
      </head>
      <body>
        Tomatometer 5 Reviews
      </body>
    </html>
    """

    parsed = _parse_rt_movie_page(html)

    assert parsed["review_count"] == 5
    assert parsed["tomatometer"] == 73.0


def test_fetch_rt_title_baseline_reports_fetch_failure_diagnostics(monkeypatch):
    def fake_fetch_text(url: str) -> str:
        raise RuntimeError("blocked")

    monkeypatch.setattr("scrapers.rt_client._fetch_text", fake_fetch_text)

    baseline = fetch_rt_title_baseline("Wuthering Heights", "m/wuthering_heights_2026")

    assert baseline["available"] is False
    assert baseline["diagnostics"]["fetch_status"] == "failed"
    assert "blocked" in baseline["diagnostics"]["message"]


def test_fetch_rt_title_baseline_reports_resolution_failure_diagnostics(monkeypatch):
    def fake_resolve(title: str):
        raise RuntimeError("search blocked")

    monkeypatch.setattr("scrapers.rt_client._resolve_rt_title_match", fake_resolve)

    baseline = fetch_rt_title_baseline("Animal Farm", None)

    assert baseline["available"] is False
    assert baseline["diagnostics"]["resolution_status"] == "failed"
    assert "search blocked" in baseline["diagnostics"]["message"]


def test_resolve_rt_title_match_rejects_low_confidence(monkeypatch):
    html = """
    <a href="/m/random_movie">Random Movie</a>
    <a href="/m/another_random_movie">Another Random Movie</a>
    """

    monkeypatch.setattr("scrapers.rt_client._fetch_text", lambda url: html)

    scores = {
        "random movie": 0.62,
        "another random movie": 0.6,
    }

    def fake_match_title(candidate, options):
        option = options[0]
        return {"match": option, "confidence": scores[option], "normalized_candidate": candidate.lower()}

    monkeypatch.setattr("scrapers.rt_client.match_title", fake_match_title)

    resolution = _resolve_rt_title_match("Superman")

    assert resolution["path"] is None
    assert resolution["confidence"] == 0.62
    assert "confidently resolve" in resolution["reason"]


def test_resolve_rt_title_match_rejects_ambiguous_top_match(monkeypatch):
    html = """
    <a href="/m/superman_2025">Superman 2025</a>
    <a href="/m/superman_legacy">Superman Legacy</a>
    """

    monkeypatch.setattr("scrapers.rt_client._fetch_text", lambda url: html)

    scores = {
        "superman 2025": 0.91,
        "superman legacy": 0.895,
    }

    def fake_match_title(candidate, options):
        option = options[0]
        return {"match": option, "confidence": scores[option], "normalized_candidate": candidate.lower()}

    monkeypatch.setattr("scrapers.rt_client.match_title", fake_match_title)

    resolution = _resolve_rt_title_match("Superman")

    assert resolution["path"] is None
    assert resolution["confidence"] == 0.91
    assert "ambiguous" in resolution["reason"]


def test_fetch_rt_title_baseline_reports_ambiguous_resolution(monkeypatch):
    monkeypatch.setattr(
        "scrapers.rt_client._resolve_rt_title_match",
        lambda title: {"path": None, "confidence": 0.9, "reason": "Rotten Tomatoes title search was ambiguous."},
    )

    baseline = fetch_rt_title_baseline("Superman", None)

    assert baseline["available"] is False
    assert baseline["rt_title_path"] is None
    assert baseline["diagnostics"]["resolution_status"] == "not_found"
    assert baseline["diagnostics"]["resolution_confidence"] == 0.9
    assert "ambiguous" in baseline["diagnostics"]["message"]

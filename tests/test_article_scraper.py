import warnings

from bs4 import XMLParsedAsHTMLWarning

from scrapers.article_scraper import ArticleScraper
from scrapers.base_scraper import PublicationConfig, SourceRule


def _build_scraper() -> ArticleScraper:
    publication = PublicationConfig(
        publication_id="test_publication",
        outlet_name="Test Outlet",
        approved_publication=True,
        source_type="article",
        critic_names=["Test Critic"],
    )
    rule = SourceRule(
        publication_id="test_publication",
        adapter="article",
        allowed_url_prefixes=["https://example.com/"],
        review_url_keywords=["review"],
    )
    return ArticleScraper(publication, rule)


def test_parse_article_html_extracts_shared_fields():
    scraper = _build_scraper()
    html = """
    <html>
      <head>
        <title>Example Review Title</title>
        <meta property="og:url" content="https://example.com/review/test-review" />
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "headline": "Test Review Headline",
            "datePublished": "2026-04-21T09:00:00Z",
            "reviewRating": {
              "ratingValue": "3",
              "bestRating": "4"
            }
          }
        </script>
      </head>
      <body>
        <p>First paragraph of the review.</p>
        <p>Second paragraph of the review.</p>
      </body>
    </html>
    """

    result = scraper.parse_article_html("https://example.com/review/test-review", html)

    assert result["headline"] == "Test Review Headline"
    assert result["published_at"] == "2026-04-21T09:00:00Z"
    assert result["raw_score"] == "3/4"
    assert "First paragraph" in result["body_text"]
    assert result["canonical_url"] == "https://example.com/review/test-review"
    assert result["critic_name"] == "Test Critic"
    assert result["critic_names"] == ["Test Critic"]


def test_parse_article_html_does_not_infer_score_from_plain_review_text():
    scraper = _build_scraper()
    html = """
    <html>
      <head>
        <title>Review Title</title>
        <meta property="article:published_time" content="2026-04-21T09:00:00Z" />
      </head>
      <body>
        <article>
          <p>The movie world is awash in fantasy, and that is a problem.</p>
          <p>A mediocre fantasy is a transparent emptiness.</p>
        </article>
      </body>
    </html>
    """

    result = scraper.parse_article_html("https://example.com/review/plain-text", html)

    assert result["raw_score"] is None


def test_parse_article_html_suppresses_xml_as_html_warning():
    scraper = _build_scraper()
    html = """<?xml version="1.0" encoding="UTF-8"?>
    <rss>
      <channel>
        <item>
          <title>Example XML Review</title>
          <description><![CDATA[<p>First paragraph.</p><p>Second paragraph.</p>]]></description>
        </item>
      </channel>
    </rss>
    """

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        scraper.parse_article_html("https://example.com/review/xml-review", html)

    assert not any(issubclass(item.category, XMLParsedAsHTMLWarning) for item in caught)


def test_parse_article_html_prefers_configured_selectors():
    publication = PublicationConfig(
        publication_id="selector_publication",
        outlet_name="Selector Outlet",
        approved_publication=True,
        source_type="article",
        critic_names=["Selector Critic"],
    )
    rule = SourceRule(
        publication_id="selector_publication",
        adapter="article",
        headline_selectors=["h1.custom-headline"],
        published_at_selectors=["time.pubdate::attr(datetime)"],
        body_selectors=["div.review-body p"],
        score_selectors=["span.grade"],
        canonical_url_selectors=["link[rel='canonical']::attr(href)"],
    )
    scraper = ArticleScraper(publication, rule)
    html = """
    <html>
      <head>
        <title>Fallback Title</title>
        <link rel="canonical" href="https://example.com/review/configured" />
      </head>
      <body>
        <h1 class="custom-headline">Configured Headline</h1>
        <time class="pubdate" datetime="2026-04-21T12:34:56Z"></time>
        <span class="grade">B+</span>
        <div class="review-body">
          <p>Configured first paragraph.</p>
          <p>Configured second paragraph.</p>
        </div>
      </body>
    </html>
    """

    result = scraper.parse_article_html("https://example.com/review/configured", html)

    assert result["headline"] == "Configured Headline"
    assert result["published_at"] == "2026-04-21T12:34:56Z"
    assert result["raw_score"] == "B+"
    assert result["body_text"] == "Configured first paragraph.\n\nConfigured second paragraph."
    assert result["canonical_url"] == "https://example.com/review/configured"


def test_parse_article_html_warns_on_malformed_json_ld():
    scraper = _build_scraper()
    html = """
    <html>
      <head>
        <script type="application/ld+json">{invalid json</script>
      </head>
      <body>
        <article><p>Body copy.</p></article>
      </body>
    </html>
    """

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        scraper.parse_article_html("https://example.com/review/bad-jsonld", html)

    assert any("Malformed JSON-LD block" in str(item.message) for item in caught)

from discover_reviews import ReviewDiscoverer


class FakeScraper:
    def __init__(self, publication_id, outlet_name, records):
        self.publication = type(
            "Publication",
            (),
            {"publication_id": publication_id, "outlet_name": outlet_name},
        )()
        self._records = records

    def list_recent_urls(self):
        return [record["source_url"] for record in self._records]

    def scrape(self, url):
        return next(record for record in self._records if record["source_url"] == url)


def test_review_discoverer_filters_and_ranks_matches():
    discoverer = ReviewDiscoverer()
    fake_scrapers = [
        FakeScraper(
            "pub1",
            "Outlet One",
            [
                {
                    "source_url": "https://example.com/a",
                    "canonical_url": "https://example.com/a",
                    "headline": "Superman review: a strong return",
                    "published_at": "2026-01-01T00:00:00Z",
                    "raw_score": None,
                },
                {
                    "source_url": "https://example.com/b",
                    "canonical_url": "https://example.com/b",
                    "headline": "Batman review",
                    "published_at": "2026-01-01T00:00:00Z",
                    "raw_score": None,
                },
            ],
        ),
        FakeScraper(
            "pub2",
            "Outlet Two",
            [
                {
                    "source_url": "https://example.org/c",
                    "canonical_url": "https://example.org/c",
                    "headline": "Superman (2026) reviewed",
                    "published_at": "2026-01-02T00:00:00Z",
                    "raw_score": "3/4",
                }
            ],
        ),
    ]
    discoverer.build_scrapers = lambda: fake_scrapers

    results = discoverer.discover("Superman", publication_workers=2, scrape_workers=2, min_confidence=0.6)

    assert len(results) == 2
    assert results[0]["match_confidence"] >= results[1]["match_confidence"]
    assert {result["publication_id"] for result in results} == {"pub1", "pub2"}
    assert all("review_likeness" in result for result in results)


def test_review_discoverer_respects_max_publications():
    discoverer = ReviewDiscoverer()
    fake_scrapers = [
        FakeScraper("pub1", "Outlet One", [{"source_url": "https://a", "canonical_url": "https://a", "headline": "Movie review", "published_at": None, "raw_score": None}]),
        FakeScraper("pub2", "Outlet Two", [{"source_url": "https://b", "canonical_url": "https://b", "headline": "Movie review", "published_at": None, "raw_score": None}]),
    ]
    discoverer.build_scrapers = lambda: fake_scrapers

    results = discoverer.discover("Movie", max_publications=1, publication_workers=1, scrape_workers=1, min_confidence=0.1)

    assert len(results) == 1
    assert results[0]["publication_id"] == "pub1"


def test_review_discoverer_filters_low_review_likeness_candidates():
    discoverer = ReviewDiscoverer()
    fake_scrapers = [
        FakeScraper(
            "pub1",
            "Outlet One",
            [
                {
                    "source_url": "https://example.com/newsletter",
                    "canonical_url": "https://example.com/newsletter",
                    "headline": "ISSUE #119",
                    "published_at": "2026-01-01T00:00:00Z",
                    "raw_score": None,
                    "body_text": "Welcome back to our newsletter." * 20,
                }
            ],
        )
    ]
    discoverer.build_scrapers = lambda: fake_scrapers

    results = discoverer.discover("Superman", publication_workers=1, scrape_workers=1, min_confidence=0.1, min_review_likeness=0.45)

    assert results == []


def test_review_discoverer_prioritizes_title_matching_urls_before_scraping():
    discoverer = ReviewDiscoverer()
    scraped_urls = []

    class TrackingScraper(FakeScraper):
        def list_recent_urls(self):
            return [
                "https://example.com/reviews/another-film-review",
                "https://example.com/reviews/animal-farm-review",
                "https://example.com/reviews/something-else-review",
            ]

        def scrape(self, url):
            scraped_urls.append(url)
            return {
                "source_url": url,
                "canonical_url": url,
                "headline": "Animal Farm review" if "animal-farm" in url else "Other review",
                "published_at": "2026-01-01T00:00:00Z",
                "raw_score": None,
                "body_text": "Review body",
            }

    discoverer.build_scrapers = lambda: [TrackingScraper("pub1", "Outlet One", [])]

    results = discoverer.discover(
        "Animal Farm",
        publication_workers=1,
        scrape_workers=1,
        max_urls_per_publication=1,
        min_confidence=0.1,
    )

    assert len(results) == 1
    assert scraped_urls == ["https://example.com/reviews/animal-farm-review"]

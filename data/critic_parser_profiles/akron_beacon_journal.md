# Parser Profile: akron_beacon_journal

Review and refine the JSON block below.

```json
{
  "publication_id": "akron_beacon_journal",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.beaconjournal.com",
  "allowed_url_prefixes": [
    "https://www.beaconjournal.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Akron Beacon Journal with sample_url='https://www.beaconjournal.com/story/entertainment/movies/2026/04/21/michael-movie-review-performances-cant-save-flawed-biopic-abouit-legend/89700346007/'. Refine selectors after inspection.",
  "sample_url": "https://www.beaconjournal.com/story/entertainment/movies/2026/04/21/michael-movie-review-performances-cant-save-flawed-biopic-abouit-legend/89700346007/",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

# Parser Profile: financial_times

Review and refine the JSON block below.

```json
{
  "publication_id": "financial_times",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.ft.com",
  "allowed_url_prefixes": [
    "https://www.ft.com/content/"
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
  "notes": "Stub generated for Financial Times with sample_url='https://www.ft.com/content/df6b92f4-3498-4d78-8695-1f490b1171cf'. Refine selectors after inspection.",
  "sample_url": "https://www.ft.com/content/df6b92f4-3498-4d78-8695-1f490b1171cf",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

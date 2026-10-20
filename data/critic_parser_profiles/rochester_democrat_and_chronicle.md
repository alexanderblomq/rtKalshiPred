# Parser Profile: rochester_democrat_and_chronicle

Review and refine the JSON block below.

```json
{
  "publication_id": "rochester_democrat_and_chronicle",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.newspapers.com",
  "allowed_url_prefixes": [
    "https://www.newspapers.com/article/"
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
  "notes": "Stub generated for Rochester Democrat and Chronicle with sample_url='https://www.newspapers.com/article/democrat-and-chronicle-legend-12/195692085/'. Refine selectors after inspection.",
  "sample_url": "https://www.newspapers.com/article/democrat-and-chronicle-legend-12/195692085/",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

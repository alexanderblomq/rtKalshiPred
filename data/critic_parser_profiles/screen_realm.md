# Parser Profile: screen_realm

Review and refine the JSON block below.

```json
{
  "publication_id": "screen_realm",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://screenrealm.com",
  "allowed_url_prefixes": [
    "https://screenrealm.com"
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
  "notes": "Stub generated for Screen Realm with sample_url='https://screenrealm.com/project-hail-mary-movie-review-ryan-gosling-2026/'. Refine selectors after inspection.",
  "sample_url": "https://screenrealm.com/project-hail-mary-movie-review-ryan-gosling-2026/",
  "observed_error": "URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1081)>"
}
```

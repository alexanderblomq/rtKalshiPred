# Parser Profile: brandon_judell_medium

Review and refine the JSON block below.

```json
{
  "publication_id": "brandon_judell_medium",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://brandonjudell.medium.com",
  "allowed_url_prefixes": [
    "https://brandonjudell.medium.com"
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
  "notes": "Stub generated for Brandon Judell (Medium) with sample_url='https://brandonjudell.medium.com/14b3d088611e?source=friends_link&sk=889e1eb20fb8ae91c970d73d9335395f'. Refine selectors after inspection.",
  "sample_url": "https://brandonjudell.medium.com/14b3d088611e?source=friends_link&sk=889e1eb20fb8ae91c970d73d9335395f",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

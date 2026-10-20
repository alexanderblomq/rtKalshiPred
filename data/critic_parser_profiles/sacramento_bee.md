# Parser Profile: sacramento_bee

Review and refine the JSON block below.

```json
{
  "publication_id": "sacramento_bee",
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
  "notes": "Stub generated for Sacramento Bee with sample_url='https://www.newspapers.com/article/the-sacramento-bee-legend-12/195693169/'. Refine selectors after inspection.",
  "sample_url": "https://www.newspapers.com/article/the-sacramento-bee-legend-12/195693169/",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

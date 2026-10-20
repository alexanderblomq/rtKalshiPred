# Parser Profile: cracked

Review and refine the JSON block below.

```json
{
  "publication_id": "cracked",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.cracked.com",
  "allowed_url_prefixes": [
    "https://www.cracked.com"
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
  "notes": "Stub generated for Cracked with sample_url='https://www.cracked.com/article_46276_brett-goldstein-isnt-afraid-to-say-men-is-bad.html'. Refine selectors after inspection.",
  "sample_url": "https://www.cracked.com/article_46276_brett-goldstein-isnt-afraid-to-say-men-is-bad.html",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

# Parser Profile: denver_rocky_mountain_news

Review and refine the JSON block below.

```json
{
  "publication_id": "denver_rocky_mountain_news",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.newspapers.com",
  "allowed_url_prefixes": [
    "https://www.newspapers.com"
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
  "notes": "Stub generated for Denver Rocky Mountain News with sample_url='https://www.newspapers.com/article/the-albuquerque-tribune-fight-club/195614021/'. Refine selectors after inspection.",
  "sample_url": "https://www.newspapers.com/article/the-albuquerque-tribune-fight-club/195614021/",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

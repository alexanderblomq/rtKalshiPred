# Parser Profile: everything_s_interesting

Review and refine the JSON block below.

```json
{
  "publication_id": "everything_s_interesting",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://medium.com",
  "allowed_url_prefixes": [
    "https://medium.com/everythings-interesting/"
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
  "notes": "Stub generated for Everything's Interesting with sample_url='https://medium.com/everythings-interesting/psycho-killer-review-a-movie-out-of-time-so-let-s-start-the-reclamation-now-04e5b5302efe?sk=dd1875c0ef37d2f09a9938f779b063bd'. Refine selectors after inspection.",
  "sample_url": "https://medium.com/everythings-interesting/psycho-killer-review-a-movie-out-of-time-so-let-s-start-the-reclamation-now-04e5b5302efe?sk=dd1875c0ef37d2f09a9938f779b063bd",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

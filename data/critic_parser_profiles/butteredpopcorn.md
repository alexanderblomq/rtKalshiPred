# Parser Profile: butteredpopcorn

Review and refine the JSON block below.

```json
{
  "publication_id": "butteredpopcorn",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.butteredpopcornmovies.com",
  "allowed_url_prefixes": [
    "https://www.butteredpopcornmovies.com"
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
  "notes": "Stub generated for ButteredPopcorn with sample_url='https://www.butteredpopcornmovies.com/sebastian-movie-review-sundance-2024.html'. Refine selectors after inspection.",
  "sample_url": "https://www.butteredpopcornmovies.com/sebastian-movie-review-sundance-2024.html",
  "observed_error": "URLError: <urlopen error [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:1081)>"
}
```

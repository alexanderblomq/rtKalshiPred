# Parser Profile: los_angeles_sentinel

Review and refine the JSON block below.

```json
{
  "publication_id": "los_angeles_sentinel",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://lasentinel.net",
  "allowed_url_prefixes": [
    "https://lasentinel.net"
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
  "notes": "Stub generated for Los Angeles Sentinel with sample_url='https://lasentinel.net/they-will-kill-you-crowns-zazie-beetz-a-full%e2%80%91on-warrioress.html'. Refine selectors after inspection.",
  "sample_url": "https://lasentinel.net/they-will-kill-you-crowns-zazie-beetz-a-full%e2%80%91on-warrioress.html",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

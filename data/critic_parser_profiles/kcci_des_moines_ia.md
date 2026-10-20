# Parser Profile: kcci_des_moines_ia

Review and refine the JSON block below.

```json
{
  "publication_id": "kcci_des_moines_ia",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://bit.ly",
  "allowed_url_prefixes": [
    "https://bit.ly"
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
  "notes": "Stub generated for KCCI (Des Moines, IA) with sample_url='https://bit.ly/4mClkKL'. Refine selectors after inspection.",
  "sample_url": "https://bit.ly/4mClkKL",
  "observed_error": "URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)>"
}
```

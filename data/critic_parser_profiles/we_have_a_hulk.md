# Parser Profile: we_have_a_hulk

Review and refine the JSON block below.

```json
{
  "publication_id": "we_have_a_hulk",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://wehaveahulk.co.uk",
  "allowed_url_prefixes": [
    "https://wehaveahulk.co.uk"
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
  "notes": "Stub generated for We Have a Hulk with sample_url='https://wehaveahulk.co.uk/tron-ares-review-a-shiny-but-shallow-long-awaited-threequel/'. Refine selectors after inspection.",
  "sample_url": "https://wehaveahulk.co.uk/tron-ares-review-a-shiny-but-shallow-long-awaited-threequel/",
  "observed_error": "URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1081)>"
}
```

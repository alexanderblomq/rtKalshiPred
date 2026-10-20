# Parser Profile: native_viewpoint

Review and refine the JSON block below.

```json
{
  "publication_id": "native_viewpoint",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://nativeviewpoint.com",
  "allowed_url_prefixes": [
    "https://nativeviewpoint.com"
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
  "notes": "Stub generated for Native Viewpoint with sample_url='https://nativeviewpoint.com/nativenerd-review-the-fantastic-four-first-steps/'. Refine selectors after inspection.",
  "sample_url": "https://nativeviewpoint.com/nativenerd-review-the-fantastic-four-first-steps/",
  "observed_error": "URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1081)>"
}
```

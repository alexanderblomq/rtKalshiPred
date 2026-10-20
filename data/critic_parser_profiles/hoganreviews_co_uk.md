# Parser Profile: hoganreviews_co_uk

Review and refine the JSON block below.

```json
{
  "publication_id": "hoganreviews_co_uk",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://hoganreviews.co.uk",
  "allowed_url_prefixes": [
    "https://hoganreviews.co.uk"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.site-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time.entry-date.published::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a.url.fn",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for hoganreviews.co.uk with sample_url='https://hoganreviews.co.uk/2026/01/10/the-fantastic-four-first-steps-review/'. Refine selectors after inspection.",
  "sample_url": "https://hoganreviews.co.uk/2026/01/10/the-fantastic-four-first-steps-review/",
  "observed": {
    "title_tag": "The Fantastic Four: First Steps Review \u2013 Hogan Reviews",
    "h1_text": "Hogan Reviews",
    "canonical_link": "https://hoganreviews.co.uk/2026/01/10/the-fantastic-four-first-steps-review/"
  }
}
```

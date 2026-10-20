# Parser Profile: the_queer_review

Review and refine the JSON block below.

```json
{
  "publication_id": "the_queer_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://thequeerreview.com",
  "allowed_url_prefixes": [
    "https://thequeerreview.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.post-title.entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time.post-date.updated::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.post-content.clear p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "span.author-name",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for The Queer Review with sample_url='https://thequeerreview.com/2026/01/28/sundance-2026-film-review-public-access/'. Refine selectors after inspection.",
  "sample_url": "https://thequeerreview.com/2026/01/28/sundance-2026-film-review-public-access/",
  "observed": {
    "title_tag": "Sundance 2026 Film Review: Public Access \u2605\u2605\u26051/2 \u2013 The Queer Review",
    "h1_text": "Sundance 2026 Film Review: Public Access \u2605\u2605\u26051/2",
    "canonical_link": "https://thequeerreview.com/2026/01/28/sundance-2026-film-review-public-access/"
  }
}
```

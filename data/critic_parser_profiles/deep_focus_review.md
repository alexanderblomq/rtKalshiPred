# Parser Profile: deep_focus_review

Review and refine the JSON block below.

```json
{
  "publication_id": "deep_focus_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.deepfocusreview.com",
  "allowed_url_prefixes": [
    "https://www.deepfocusreview.com"
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
      "time[itemprop='datePublished'].df-date::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article#review.df-review.single-review p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "meta[itemprop='ratingValue']",
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "h4[itemprop='author']",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Deep Focus Review with sample_url='https://www.deepfocusreview.com/definitives/red-sorghum/'. Refine selectors after inspection.",
  "sample_url": "https://www.deepfocusreview.com/definitives/red-sorghum/",
  "observed": {
    "title_tag": "Red Sorghum (2026) | The Definitives | Deep Focus Review",
    "h1_text": "Red Sorghum (1988)",
    "canonical_link": "https://www.deepfocusreview.com/definitives/red-sorghum/"
  }
}
```

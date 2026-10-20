# Parser Profile: loud_and_clear_reviews

Review and refine the JSON block below.

```json
{
  "publication_id": "loud_and_clear_reviews",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://loudandclearreviews.com",
  "allowed_url_prefixes": [
    "https://loudandclearreviews.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.elementor-heading-title.elementor-size-default",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div.elementor-element.elementor-element-196908d",
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "meta[name='author']::attr(content)",
      "meta[name='author']",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Loud and Clear Reviews with sample_url='https://loudandclearreviews.com/michael-2026-movie-review/'. Refine selectors after inspection.",
  "sample_url": "https://loudandclearreviews.com/michael-2026-movie-review/",
  "observed": {
    "title_tag": "Michael (2026) Review: Another Glorified Music Video - Loud And Clear Reviews",
    "h1_text": "Michael (2026) Review: Another Glorified Music Video",
    "canonical_link": "https://loudandclearreviews.com/michael-2026-movie-review/"
  }
}
```

# Parser Profile: ripple_effects

Review and refine the JSON block below.

```json
{
  "publication_id": "ripple_effects",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://rippleeffects.reviews/movies-reviewed/",
  "allowed_url_prefixes": [
    "https://rippleeffects.reviews/20"
  ],
  "review_url_keywords": [
    "/20"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.entry-title",
      "meta[property='og:title']::attr(content)",
      "h1"
    ],
    "published_at_selectors": [
      "time.entry-date.published::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "meta[itemprop='ratingValue']::attr(content)",
      ".rating",
      "[class*='rating']"
    ],
    "critic_name_selectors": [
      "a[rel='author'].author-link",
      "span.author.vcard a",
      "span.author.vcard"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Refined for Ripple Effects' date-based WordPress permalinks and movie-specific landing page so discovery stops treating the broader books/about navigation as review candidates.",
  "sample_url": "https://rippleeffects.reviews/2025/06/26/materialists-is-a-film-jane-austen-would-like/",
  "observed": {
    "title_tag": "‘Materialists’ is a film Jane Austen would like – Ripple Effects",
    "h1_text": "‘Materialists’ is a film Jane Austen would like",
    "canonical_link": "https://rippleeffects.reviews/2025/06/26/materialists-is-a-film-jane-austen-would-like/"
  }
}
```

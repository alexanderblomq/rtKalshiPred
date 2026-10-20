# Parser Profile: flixchatter_film_blog

Review and refine the JSON block below.

```json
{
  "publication_id": "flixchatter_film_blog",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://flixchatter.net",
  "allowed_url_prefixes": [
    "https://flixchatter.net"
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
  "notes": "Stub generated for FlixChatter Film Blog with sample_url='https://flixchatter.net/2026/04/18/mspiff-2026-honeyjoon-2025-a-breezy-delightful-mother-daughter-comedy-about-navigating-grief-set-in-the-azores/'. Refine selectors after inspection.",
  "sample_url": "https://flixchatter.net/2026/04/18/mspiff-2026-honeyjoon-2025-a-breezy-delightful-mother-daughter-comedy-about-navigating-grief-set-in-the-azores/",
  "observed": {
    "title_tag": "MSPIFF 2026 Review: HONEYJOON (2025) \u2013 A breezy, delightful mother-daughter comedy about navigating grief, set in the Azores \u2013 FLIXCHATTER FILM BLOG",
    "h1_text": "FLIXCHATTER FILM BLOG",
    "canonical_link": "https://flixchatter.net/2026/04/18/mspiff-2026-honeyjoon-2025-a-breezy-delightful-mother-daughter-comedy-about-navigating-grief-set-in-the-azores/"
  }
}
```

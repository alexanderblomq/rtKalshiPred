# Parser Profile: empire_magazine

Review and refine the JSON block below.

```json
{
  "publication_id": "empire_magazine",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.empireonline.com/movies/reviews/",
  "allowed_url_prefixes": [
    "https://www.empireonline.com/movies/reviews/"
  ],
  "review_url_keywords": [
    "/movies/reviews/"
  ],
  "selectors": {
    "headline_selectors": [
      "h1[class*='title_h1']",
      "meta[property='og:title']::attr(content)",
      "h1"
    ],
    "published_at_selectors": [
      "time::attr(datetime)",
      "meta[property='article:published_time']::attr(content)"
    ],
    "body_selectors": [
      "article[class*='article'] p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div[class*='ratings_review-rating']",
      "meta[itemprop='ratingValue']::attr(content)",
      ".rating"
    ],
    "critic_name_selectors": [
      "[class*='authorDate_author__name']",
      "[class*='authorDate_author__'] a",
      "meta[name='author']::attr(content)"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Refined for Empire's dedicated /movies/reviews/ stream and hashed classnames, using wildcard class selectors that are stable across CSS module renames.",
  "sample_url": "https://www.empireonline.com/movies/reviews/michael-2026/",
  "observed": {
    "title_tag": "Michael Review – 'Cosplay tribute with no point-of-view'",
    "h1_text": "Michael (2026) Review",
    "canonical_link": "https://www.empireonline.com/movies/reviews/michael-2026/"
  }
}
```

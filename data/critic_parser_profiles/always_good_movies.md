# Parser Profile: always_good_movies

Review and refine the JSON block below.

```json
{
  "publication_id": "always_good_movies",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://alwaysgoodmovies.com/reviews",
  "allowed_url_prefixes": [
    "https://alwaysgoodmovies.com/reviews/"
  ],
  "review_url_keywords": [
    "/reviews/"
  ],
  "selectors": {
    "headline_selectors": [
      "meta[property='og:title']::attr(content)",
      "article h1",
      "h1"
    ],
    "published_at_selectors": [
      "time.published.dt-published::attr(datetime)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article.hentry p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "meta[itemprop='ratingValue']::attr(content)",
      ".rating",
      "[class*='rating']"
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
  "notes": "Refined for Always Good Movies' Squarespace /reviews/ article collection so discovery focuses on article pages instead of tag and category indexes, and headline extraction prefers the OG title over the empty logo H1.",
  "sample_url": "https://alwaysgoodmovies.com/reviews/a-poet-2026",
  "observed": {
    "title_tag": "A Poet (2026) — Always Good Movies",
    "canonical_link": "https://alwaysgoodmovies.com/reviews/a-poet-2026"
  }
}
```

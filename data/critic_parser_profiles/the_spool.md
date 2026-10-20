# Parser Profile: the_spool

Review and refine the JSON block below.

```json
{
  "publication_id": "the_spool",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://thespool.net",
  "allowed_url_prefixes": [
    "https://thespool.net"
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
      "article.entry.post p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div.single-score",
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
  "notes": "Stub generated for The Spool with sample_url='https://thespool.net/reviews/film-review-pizza-movie-hulu-2026-gaten-matarazzo/'. Refine selectors after inspection.",
  "sample_url": "https://thespool.net/reviews/film-review-pizza-movie-hulu-2026-gaten-matarazzo/",
  "observed": {
    "title_tag": "Pizza Movie satisfies your stoner movie munchies   | The Spool",
    "h1_text": null,
    "canonical_link": "https://thespool.net/reviews/film-review-pizza-movie-hulu-2026-gaten-matarazzo/"
  }
}
```

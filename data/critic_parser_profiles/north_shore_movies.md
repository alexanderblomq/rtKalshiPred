# Parser Profile: north_shore_movies

Review and refine the JSON block below.

```json
{
  "publication_id": "north_shore_movies",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://northshoremovies.wpcomstaging.com",
  "allowed_url_prefixes": [
    "https://northshoremovies.wpcomstaging.com"
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
      "time.entry-date::attr(datetime)",
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
      "a[rel='author'].url.fn",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for North Shore Movies with sample_url='https://northshoremovies.wpcomstaging.com/2026/04/10/review-outcome/'. Refine selectors after inspection.",
  "sample_url": "https://northshoremovies.wpcomstaging.com/2026/04/10/review-outcome/",
  "observed": {
    "title_tag": "Review \u2013 Outcome | NorthShoreMovies.net",
    "h1_text": "NorthShoreMovies.net",
    "canonical_link": "https://northshoremovies.wpcomstaging.com/2026/04/10/review-outcome/"
  }
}
```

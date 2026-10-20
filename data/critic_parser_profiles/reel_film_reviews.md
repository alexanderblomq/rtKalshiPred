# Parser Profile: reel_film_reviews

Review and refine the JSON block below.

```json
{
  "publication_id": "reel_film_reviews",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://reelfilm.com",
  "allowed_url_prefixes": [
    "https://reelfilm.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article.post-36008.post p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a[rel='author']",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Reel Film Reviews with sample_url='https://reelfilm.com/thrash/'. Refine selectors after inspection.",
  "sample_url": "https://reelfilm.com/thrash/",
  "observed": {
    "title_tag": "Thrash \u2013 Reel Film Reviews",
    "h1_text": "Thrash",
    "canonical_link": "https://reelfilm.com/thrash/"
  }
}
```

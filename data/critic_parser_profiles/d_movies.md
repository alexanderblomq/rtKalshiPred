# Parser Profile: d_movies

Review and refine the JSON block below.

```json
{
  "publication_id": "d_movies",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.dmovies.org",
  "allowed_url_prefixes": [
    "https://www.dmovies.org"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.dm_title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article p",
      "main p"
    ],
    "score_selectors": [
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
  "notes": "Stub generated for D Movies with sample_url='https://www.dmovies.org/2023/10/18/sex-with-sue/'. Refine selectors after inspection.",
  "sample_url": "https://www.dmovies.org/2023/10/18/sex-with-sue/",
  "observed": {
    "title_tag": "Sex with Sue - film review",
    "h1_text": "Sex with Sue",
    "canonical_link": "https://dmovies.org/2023/10/18/sex-with-sue/"
  }
}
```

# Parser Profile: fat_guys_at_the_movies

Review and refine the JSON block below.

```json
{
  "publication_id": "fat_guys_at_the_movies",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.fatguysatthemovies.com",
  "allowed_url_prefixes": [
    "https://www.fatguysatthemovies.com"
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
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Fat Guys at the Movies with sample_url='https://www.fatguysatthemovies.com/the-toxic-avenger-movie-review/'. Refine selectors after inspection.",
  "sample_url": "https://www.fatguysatthemovies.com/the-toxic-avenger-movie-review/",
  "observed": {
    "title_tag": "\u201cThe Toxic Avenger\u201d Movie Review \u2013 Fat Guys at the Movies",
    "h1_text": "\u201cThe Toxic Avenger\u201d Movie Review",
    "canonical_link": "https://www.fatguysatthemovies.com/the-toxic-avenger-movie-review/"
  }
}
```

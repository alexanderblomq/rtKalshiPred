# Parser Profile: ign_movies

Review and refine the JSON block below.

```json
{
  "publication_id": "ign_movies",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.ign.com",
  "allowed_url_prefixes": [
    "https://www.ign.com/articles/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.display-title.jsx-684634384",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "div.jsx-2870106660.article-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "span.stack.jsx-3547261442",
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a.link.jsx-1337145738",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for IGN Movies with sample_url='https://www.ign.com/articles/michael-jackson-movie-review'. Refine selectors after inspection.",
  "sample_url": "https://www.ign.com/articles/michael-jackson-movie-review",
  "observed": {
    "title_tag": "Michael Review - IGN",
    "h1_text": "Michael Review",
    "canonical_link": "https://www.ign.com/articles/michael-jackson-movie-review"
  }
}
```

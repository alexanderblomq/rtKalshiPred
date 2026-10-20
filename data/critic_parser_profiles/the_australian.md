# Parser Profile: the_australian

Review and refine the JSON block below.

```json
{
  "publication_id": "the_australian",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.theaustralian.com.au",
  "allowed_url_prefixes": [
    "https://www.theaustralian.com.au"
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
  "notes": "Stub generated for The Australian with sample_url='https://www.theaustralian.com.au/culture/you-me-tuscany-review-a-formulaic-film-that-wastes-its-stars/news-story/11e35167dafb38b6865fa6e484da8a6e'. Refine selectors after inspection.",
  "sample_url": "https://www.theaustralian.com.au/culture/you-me-tuscany-review-a-formulaic-film-that-wastes-its-stars/news-story/11e35167dafb38b6865fa6e484da8a6e",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

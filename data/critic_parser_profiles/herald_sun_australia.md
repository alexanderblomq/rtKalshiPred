# Parser Profile: herald_sun_australia

Review and refine the JSON block below.

```json
{
  "publication_id": "herald_sun_australia",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.heraldsun.com.au",
  "allowed_url_prefixes": [
    "https://www.heraldsun.com.au/entertainment/movies/"
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
  "notes": "Stub generated for Herald Sun (Australia) with sample_url='https://www.heraldsun.com.au/entertainment/movies/the-deb-review-final-verdict-on-rebels-troubled-film-musical/news-story/f1d4d24c6f785ebcdf275540c8b0877d'. Refine selectors after inspection.",
  "sample_url": "https://www.heraldsun.com.au/entertainment/movies/the-deb-review-final-verdict-on-rebels-troubled-film-musical/news-story/f1d4d24c6f785ebcdf275540c8b0877d",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

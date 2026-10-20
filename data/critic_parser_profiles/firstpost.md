# Parser Profile: firstpost

Review and refine the JSON block below.

```json
{
  "publication_id": "firstpost",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.firstpost.com",
  "allowed_url_prefixes": [
    "https://www.firstpost.com/entertainment/"
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
  "notes": "Stub generated for Firstpost with sample_url='https://www.firstpost.com/entertainment/lee-cronins-the-mummy-movie-review-watch-this-orgy-of-horror-and-gore-with-your-eyes-wide-shut-14001376.html'. Refine selectors after inspection.",
  "sample_url": "https://www.firstpost.com/entertainment/lee-cronins-the-mummy-movie-review-watch-this-orgy-of-horror-and-gore-with-your-eyes-wide-shut-14001376.html",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

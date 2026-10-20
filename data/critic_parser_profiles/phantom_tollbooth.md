# Parser Profile: phantom_tollbooth

Review and refine the JSON block below.

```json
{
  "publication_id": "phantom_tollbooth",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://tollbooth.org",
  "allowed_url_prefixes": [
    "https://tollbooth.org"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.title.page-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "time.datetime::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article.node.node--type-post-movie p",
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
  "notes": "Stub generated for Phantom Tollbooth with sample_url='https://tollbooth.org/movie-reviews/proud-priness'. Refine selectors after inspection.",
  "sample_url": "https://tollbooth.org/movie-reviews/proud-priness",
  "observed": {
    "title_tag": "The Proud Priness | The Phantom Tollbooth",
    "h1_text": "The Proud Priness",
    "canonical_link": "https://tollbooth.org/movie-reviews/proud-priness"
  }
}
```

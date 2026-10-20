# Parser Profile: inbetweendrafts

Review and refine the JSON block below.

```json
{
  "publication_id": "inbetweendrafts",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://inbetweendrafts.com",
  "allowed_url_prefixes": [
    "https://inbetweendrafts.com"
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
      "div.post-content p",
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
  "notes": "Stub generated for InBetweenDrafts with sample_url='https://inbetweendrafts.com/normal-review-bob-odenkirk/'. Refine selectors after inspection.",
  "sample_url": "https://inbetweendrafts.com/normal-review-bob-odenkirk/",
  "observed": {
    "title_tag": "Normal Review - InBetweenDrafts",
    "h1_text": "\u2018Normal\u2019 review: A bloody blend of genres",
    "canonical_link": "https://inbetweendrafts.com/normal-review-bob-odenkirk/"
  }
}
```

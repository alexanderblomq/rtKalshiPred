# Parser Profile: in_review_online

Review and refine the JSON block below.

```json
{
  "publication_id": "in_review_online",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://inreviewonline.com",
  "allowed_url_prefixes": [
    "https://inreviewonline.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.is-title.post-title-alt",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time.post-date::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.post-content.description p",
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
  "notes": "Stub generated for In Review Online with sample_url='https://inreviewonline.com/2026/04/21/michael-2026-review/'. Refine selectors after inspection.",
  "sample_url": "https://inreviewonline.com/2026/04/21/michael-2026-review/",
  "observed": {
    "title_tag": "Michael \u2014 Antoine Fuqua [Review] | In Review Online",
    "h1_text": "Michael \u2014 Antoine Fuqua [Review]",
    "canonical_link": "https://inreviewonline.com/2026/04/21/michael-2026-review/"
  }
}
```

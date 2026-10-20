# Parser Profile: jordy_reviews_it

Review and refine the JSON block below.

```json
{
  "publication_id": "jordy_reviews_it",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://jordyreviewsit.com",
  "allowed_url_prefixes": [
    "https://jordyreviewsit.com"
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
      "time.entry-date.published::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div#entry-content.entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a.url.fn",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Jordy Reviews It with sample_url='https://jordyreviewsit.com/2026/04/18/lee-cronins-the-mummy-is-a-soulless-evil-dead-movie/'. Refine selectors after inspection.",
  "sample_url": "https://jordyreviewsit.com/2026/04/18/lee-cronins-the-mummy-is-a-soulless-evil-dead-movie/",
  "observed": {
    "title_tag": "Lee Cronin\u2019s THE MUMMY Is a Soulless Evil Dead Movie \u2013 Jordy Reviews It",
    "h1_text": "Lee Cronin\u2019s THE MUMMY Is a Soulless Evil Dead\u00a0Movie",
    "canonical_link": "https://jordyreviewsit.com/2026/04/18/lee-cronins-the-mummy-is-a-soulless-evil-dead-movie/"
  }
}
```

# Parser Profile: nuha_hassan_medium

Review and refine the JSON block below.

```json
{
  "publication_id": "nuha_hassan_medium",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://nuhahassan.medium.com",
  "allowed_url_prefixes": [
    "https://nuhahassan.medium.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1#b4c4.pw-post-title.hm",
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
  "notes": "Stub generated for Nuha Hassan (Medium) with sample_url='https://nuhahassan.medium.com/pretty-lethal-2026-review-uma-thurman-72d467ecf18b?postPublishedType=repub'. Refine selectors after inspection.",
  "sample_url": "https://nuhahassan.medium.com/pretty-lethal-2026-review-uma-thurman-72d467ecf18b?postPublishedType=repub",
  "observed": {
    "title_tag": "\u2018Pretty Lethal\u2019 (2026) Review: A Great Week for Enraged Ballerinas | Medium",
    "h1_text": "\u2018Pretty Lethal\u2019 (2026) Review: A Great Week for Enraged Ballerinas",
    "canonical_link": "https://nuhahassan.medium.com/pretty-lethal-2026-review-a-great-week-for-enraged-ballerinas-72d467ecf18b"
  }
}
```

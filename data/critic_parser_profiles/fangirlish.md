# Parser Profile: fangirlish

Review and refine the JSON block below.

```json
{
  "publication_id": "fangirlish",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://fangirlish.com",
  "allowed_url_prefixes": [
    "https://fangirlish.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1[itemprop='name headline'].entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time[itemprop='datePublished'].date.published::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.post-content.entry-content p",
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
  "notes": "Stub generated for Fangirlish with sample_url='https://fangirlish.com/2026/02/19/the-calling-witch-2026-horror-review/'. Refine selectors after inspection.",
  "sample_url": "https://fangirlish.com/2026/02/19/the-calling-witch-2026-horror-review/",
  "observed": {
    "title_tag": "The Calling Witch Review: Nancy Wheeler, You've Got Some Competition - Fangirlish",
    "h1_text": "The Calling Witch Review: Nancy Wheeler, You\u2019ve Got Some Competition",
    "canonical_link": "https://fangirlish.com/2026/02/19/the-calling-witch-2026-horror-review/"
  }
}
```

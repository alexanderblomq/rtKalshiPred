# Parser Profile: the_wolfman_cometh

Review and refine the JSON block below.

```json
{
  "publication_id": "the_wolfman_cometh",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://thewolfmancometh.com",
  "allowed_url_prefixes": [
    "https://thewolfmancometh.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.site-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time.entry-date::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.entry-content.clear-fix p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div#jp-post-flair.sharedaddy.sd-rating-enabled",
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a[rel='author'].url.fn",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for The Wolfman Cometh with sample_url='https://thewolfmancometh.com/2026/04/14/normal-movie-bob-odenkirk-2025-review/'. Refine selectors after inspection.",
  "sample_url": "https://thewolfmancometh.com/2026/04/14/normal-movie-bob-odenkirk-2025-review/",
  "observed": {
    "title_tag": "Normal (2025) [REVIEW] | The Wolfman Cometh",
    "h1_text": "The Wolfman Cometh",
    "canonical_link": "https://thewolfmancometh.com/2026/04/14/normal-movie-bob-odenkirk-2025-review/"
  }
}
```

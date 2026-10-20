# Parser Profile: eyes_wide_open_medium

Review and refine the JSON block below.

```json
{
  "publication_id": "eyes_wide_open_medium",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://medium.com",
  "allowed_url_prefixes": [
    "https://medium.com/eyes-wide-open/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1#5348.pw-post-title.jb",
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
  "notes": "Stub generated for Eyes Wide Open (Medium) with sample_url='https://medium.com/eyes-wide-open/saltburn-didn-t-deserve-an-oscar-it-s-still-great-ab61eb88d657'. Refine selectors after inspection.",
  "sample_url": "https://medium.com/eyes-wide-open/saltburn-didn-t-deserve-an-oscar-it-s-still-great-ab61eb88d657",
  "observed": {
    "title_tag": "\u2018Saltburn\u2019 Didn\u2019t Deserve an Oscar \u2014 It\u2019s Still Great | by Chris Barsanti | Eyes Wide Open | Medium",
    "h1_text": "\u2018Saltburn\u2019 Didn\u2019t Deserve an Oscar \u2014 It\u2019s Still Great",
    "canonical_link": "https://medium.com/eyes-wide-open/saltburn-didn-t-deserve-an-oscar-it-s-still-great-ab61eb88d657"
  }
}
```

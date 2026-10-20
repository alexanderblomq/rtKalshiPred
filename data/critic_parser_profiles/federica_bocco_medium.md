# Parser Profile: federica_bocco_medium

Review and refine the JSON block below.

```json
{
  "publication_id": "federica_bocco_medium",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://medium.com",
  "allowed_url_prefixes": [
    "https://medium.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1#5cdb.pw-post-title.hm",
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
  "notes": "Stub generated for Federica Bocco (Medium) with sample_url='https://medium.com/@federicabocco/flash-review-james-gunns-superman-2025-8fa75a630a86'. Refine selectors after inspection.",
  "sample_url": "https://medium.com/@federicabocco/flash-review-james-gunns-superman-2025-8fa75a630a86",
  "observed": {
    "title_tag": "Flash Review: James Gunn\u2019s Superman (2025) | by Federica Bocco | Medium",
    "h1_text": "Flash Review: James Gunn\u2019s Superman (2025)",
    "canonical_link": "https://medium.com/@federicabocco/flash-review-james-gunns-superman-2025-8fa75a630a86"
  }
}
```

# Parser Profile: cinewomen

Review and refine the JSON block below.

```json
{
  "publication_id": "cinewomen",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://annleee.medium.com",
  "allowed_url_prefixes": [
    "https://annleee.medium.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1#d462.pw-post-title.hm",
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
  "notes": "Stub generated for CineWomen with sample_url='https://annleee.medium.com/cinewomen-19-c709dd248ab7'. Refine selectors after inspection.",
  "sample_url": "https://annleee.medium.com/cinewomen-19-c709dd248ab7",
  "observed": {
    "title_tag": "CineWomen: Nisha Ganatra refreshes \u2018Freaky Friday\u2019 | by Annlee Ellingson | Medium",
    "h1_text": "CineWomen: Nisha Ganatra refreshes \u2018Freaky Friday\u2019",
    "canonical_link": "https://annleee.medium.com/cinewomen-19-c709dd248ab7"
  }
}
```

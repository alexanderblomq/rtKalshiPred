# Parser Profile: reeling_reviews

Review and refine the JSON block below.

```json
{
  "publication_id": "reeling_reviews",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.reelingreviews.com",
  "allowed_url_prefixes": [
    "https://www.reelingreviews.com/reviews/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "main#main.site-main p",
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
  "notes": "Stub generated for Reeling Reviews with sample_url='https://www.reelingreviews.com/reviews/over-your-dead-body/'. Refine selectors after inspection.",
  "sample_url": "https://www.reelingreviews.com/reviews/over-your-dead-body/",
  "observed": {
    "title_tag": "Over Your Dead Body - Reeling Reviews",
    "h1_text": "Over Your Dead Body",
    "canonical_link": "https://www.reelingreviews.com/reviews/over-your-dead-body/"
  }
}
```

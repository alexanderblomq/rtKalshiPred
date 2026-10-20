# Parser Profile: blu_ray_com

Review and refine the JSON block below.

```json
{
  "publication_id": "blu_ray_com",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.blu-ray.com",
  "allowed_url_prefixes": [
    "https://www.blu-ray.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.eurostile",
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
      "div.product_rating_small2",
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
  "notes": "Stub generated for Blu-ray.com with sample_url='https://www.blu-ray.com/Michael/1797900/#Review'. Refine selectors after inspection.",
  "sample_url": "https://www.blu-ray.com/Michael/1797900/#Review",
  "observed": {
    "title_tag": "Michael (2026)",
    "h1_text": "Michael 2026",
    "canonical_link": "https://www.blu-ray.com/Michael/1797900/"
  }
}
```

# Parser Profile: family_home_theater

Review and refine the JSON block below.

```json
{
  "publication_id": "family_home_theater",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://familyhometheater.com",
  "allowed_url_prefixes": [
    "https://familyhometheater.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1#logo",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.post-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a[rel='author']",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Family Home Theater with sample_url='https://familyhometheater.com/2014/08/16/out-of-the-past-blu-ray/'. Refine selectors after inspection.",
  "sample_url": "https://familyhometheater.com/2014/08/16/out-of-the-past-blu-ray/",
  "observed": {
    "title_tag": "OUT OF THE PAST (Blu-ray) | Family Home Theater",
    "h1_text": "Family Home Theater",
    "canonical_link": "https://familyhometheater.com/2014/08/16/out-of-the-past-blu-ray/"
  }
}
```

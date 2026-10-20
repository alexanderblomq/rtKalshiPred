# Parser Profile: eye_for_film

Review and refine the JSON block below.

```json
{
  "publication_id": "eye_for_film",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.eyeforfilm.co.uk",
  "allowed_url_prefixes": [
    "https://www.eyeforfilm.co.uk"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.reviewTitleText",
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
      "div.filmrating",
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
  "notes": "Stub generated for Eye for Film with sample_url='https://www.eyeforfilm.co.uk/review/camp-2025-film-review-by-jennie-kermode'. Refine selectors after inspection.",
  "sample_url": "https://www.eyeforfilm.co.uk/review/camp-2025-film-review-by-jennie-kermode",
  "observed": {
    "title_tag": "Camp (2025) Movie Review from Eye for Film",
    "h1_text": "Camp",
    "canonical_link": null
  }
}
```

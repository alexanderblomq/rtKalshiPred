# Parser Profile: the_lamplight_review

Review and refine the JSON block below.

```json
{
  "publication_id": "the_lamplight_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://lamplightreview.com",
  "allowed_url_prefixes": [
    "https://lamplightreview.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.is-title.post-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time.post-date::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.post-content.cf p",
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
  "notes": "Stub generated for The Lamplight Review with sample_url='https://lamplightreview.com/movie-review-blades-of-the-guardians/'. Refine selectors after inspection.",
  "sample_url": "https://lamplightreview.com/movie-review-blades-of-the-guardians/",
  "observed": {
    "title_tag": "'Blades of the Guardians' Review: A Wuxia Masterclass From a Living Legend",
    "h1_text": "Movie Review: \u2018Blades of the Guardians\u2019",
    "canonical_link": "https://lamplightreview.com/movie-review-blades-of-the-guardians/"
  }
}
```

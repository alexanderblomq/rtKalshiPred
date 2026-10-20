# Parser Profile: the_wee_review

Review and refine the JSON block below.

```json
{
  "publication_id": "the_wee_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://theweereview.com",
  "allowed_url_prefixes": [
    "https://theweereview.com/review/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.post-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "time.entry-date.published::attr(datetime)",
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
      "ul.list-inline.rating",
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a.url.fn",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for The Wee Review with sample_url='https://theweereview.com/review/babystar/'. Refine selectors after inspection.",
  "sample_url": "https://theweereview.com/review/babystar/",
  "observed": {
    "title_tag": "Babystar \u2013 The Wee Review | Scotland\u2019s arts and culture magazine",
    "h1_text": "Babystar",
    "canonical_link": "https://theweereview.com/review/babystar/"
  }
}
```

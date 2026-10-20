# Parser Profile: awards_buzz

Review and refine the JSON block below.

```json
{
  "publication_id": "awards_buzz",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://awardsbuzz.com",
  "allowed_url_prefixes": [
    "https://awardsbuzz.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.tdb-title-text",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time.entry-date.updated::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article#template-id-5852.post-5852.tdb_templates p",
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
  "notes": "Stub generated for Awards Buzz with sample_url='https://awardsbuzz.com/sxsw-review-and-her-body-was-never-found-is-a-unique-captivating-display-of-marriage-in-crisis/'. Refine selectors after inspection.",
  "sample_url": "https://awardsbuzz.com/sxsw-review-and-her-body-was-never-found-is-a-unique-captivating-display-of-marriage-in-crisis/",
  "observed": {
    "title_tag": "SXSW Review: \u2018And Her Body Was Never Found\u2019 is Unique",
    "h1_text": "SXSW Review: \u2018And Her Body Was Never Found\u2019 is a Unique, Captivating Display of Marriage in Crisis",
    "canonical_link": "https://awardsbuzz.com/sxsw-review-and-her-body-was-never-found-is-a-unique-captivating-display-of-marriage-in-crisis/"
  }
}
```

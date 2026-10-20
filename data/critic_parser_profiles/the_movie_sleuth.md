# Parser Profile: the_movie_sleuth

Review and refine the JSON block below.

```json
{
  "publication_id": "the_movie_sleuth",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.spoilerfreemoviesleuth.com",
  "allowed_url_prefixes": [
    "https://www.spoilerfreemoviesleuth.com"
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
      "time.published::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div#post-body-5697603226520031219.post-body.entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a[rel='bookmark'].timestamp-link",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for The Movie Sleuth with sample_url='https://www.spoilerfreemoviesleuth.com/2026/04/criterion-corner-to-da-break-of-dawn.html?m=1'. Refine selectors after inspection.",
  "sample_url": "https://www.spoilerfreemoviesleuth.com/2026/04/criterion-corner-to-da-break-of-dawn.html?m=1",
  "observed": {
    "title_tag": "Criterion Corner: To da Break of Dawn: House Party (1990) - Reviewed",
    "h1_text": "The Movie Sleuth",
    "canonical_link": "https://www.spoilerfreemoviesleuth.com/2026/04/criterion-corner-to-da-break-of-dawn.html"
  }
}
```

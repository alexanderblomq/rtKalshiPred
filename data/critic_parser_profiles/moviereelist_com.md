# Parser Profile: moviereelist_com

Review and refine the JSON block below.

```json
{
  "publication_id": "moviereelist_com",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://moviereelist.com",
  "allowed_url_prefixes": [
    "https://moviereelist.com/review/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "time.entry-date::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article#post-43409.post-43409.review p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "article#post-43409.post-43409.review",
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
  "notes": "Stub generated for MovieReelist.com with sample_url='https://moviereelist.com/review/movie-review-dracula-a-love-tale/'. Refine selectors after inspection.",
  "sample_url": "https://moviereelist.com/review/movie-review-dracula-a-love-tale/",
  "observed": {
    "title_tag": "Movie Review - 'Dracula: A Love Tale' is the bloody gothic horror for the eternal romantic - Movie Reelist",
    "h1_text": "Movie Review \u2013 \u2018Dracula: A Love Tale\u2019 is the bloody gothic horror for the eternal romantic",
    "canonical_link": "https://moviereelist.com/review/movie-review-dracula-a-love-tale/"
  }
}
```

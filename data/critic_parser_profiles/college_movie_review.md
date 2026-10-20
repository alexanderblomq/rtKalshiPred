# Parser Profile: college_movie_review

Review and refine the JSON block below.

```json
{
  "publication_id": "college_movie_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://collegemoviereview.com",
  "allowed_url_prefixes": [
    "https://collegemoviereview.com"
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
      "meta[property='article:published_time']::attr(content)",
      "time.entry-date.published::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.entry-content p",
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
  "notes": "Stub generated for College Movie Review with sample_url='https://collegemoviereview.com/reviews/andrea-bocelli-because-i-believe/'. Refine selectors after inspection.",
  "sample_url": "https://collegemoviereview.com/reviews/andrea-bocelli-because-i-believe/",
  "observed": {
    "title_tag": "Review: Andrea Bocelli: Because I Believe - College Movie Review",
    "h1_text": "Review: Andrea Bocelli: Because I Believe",
    "canonical_link": "https://collegemoviereview.com/reviews/andrea-bocelli-because-i-believe/"
  }
}
```

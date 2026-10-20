# Parser Profile: npr

Review and refine the JSON block below.

```json
{
  "publication_id": "npr",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.npr.org",
  "allowed_url_prefixes": [
    "https://www.npr.org"
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
      "time::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "article.story p",
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
  "notes": "Stub generated for NPR with sample_url='https://www.npr.org/2026/04/10/nx-s1-5769346/the-christophers-review-ian-mckellen-michaela-coel'. Refine selectors after inspection.",
  "sample_url": "https://www.npr.org/2026/04/10/nx-s1-5769346/the-christophers-review-ian-mckellen-michaela-coel",
  "observed": {
    "title_tag": "'The Christophers' review: Ian McKellen and Michaela Coel give more than a masterclass : NPR",
    "h1_text": "In Steven Soderbergh's 'The Christophers,' an aging artist meets his match",
    "canonical_link": "https://www.npr.org/2026/04/10/nx-s1-5769346/the-christophers-review-ian-mckellen-michaela-coel"
  }
}
```

# Parser Profile: eulalie_magazine

Review and refine the JSON block below.

```json
{
  "publication_id": "eulalie_magazine",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://eulaliemagazine.com",
  "allowed_url_prefixes": [
    "https://eulaliemagazine.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1[itemprop='name'].entry-title",
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
      "div[itemprop='articleBody'].entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div.yasr-overall-rating",
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
  "notes": "Stub generated for Eulalie Magazine with sample_url='https://eulaliemagazine.com/2026/03/project-hail-mary-review-ryan-gosling-is-stellar-in-this-ambitious-adaptation/'. Refine selectors after inspection.",
  "sample_url": "https://eulaliemagazine.com/2026/03/project-hail-mary-review-ryan-gosling-is-stellar-in-this-ambitious-adaptation/",
  "observed": {
    "title_tag": "Project Hail Mary Review: Ryan Gosling is Stellar in This Ambitious Adaptation",
    "h1_text": "Project Hail Mary Review: Ryan Gosling is Stellar in This Ambitious Adaptation",
    "canonical_link": "https://eulaliemagazine.com/2026/03/project-hail-mary-review-ryan-gosling-is-stellar-in-this-ambitious-adaptation/"
  }
}
```

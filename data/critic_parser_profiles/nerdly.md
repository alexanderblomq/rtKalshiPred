# Parser Profile: nerdly

Review and refine the JSON block below.

```json
{
  "publication_id": "nerdly",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.nerdly.co.uk",
  "allowed_url_prefixes": [
    "https://www.nerdly.co.uk"
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
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
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
  "notes": "Stub generated for Nerdly with sample_url='https://www.nerdly.co.uk/2025/10/29/stiges-2025-fucktoys-review/'. Refine selectors after inspection.",
  "sample_url": "https://www.nerdly.co.uk/2025/10/29/stiges-2025-fucktoys-review/",
  "observed": {
    "title_tag": "Nerdly \u00bb Stiges 2025: \u2018Fucktoys\u2019 Review",
    "h1_text": null,
    "canonical_link": "https://www.nerdly.co.uk/2025/10/29/stiges-2025-fucktoys-review/"
  }
}
```

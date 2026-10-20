# Parser Profile: review_film_review

Review and refine the JSON block below.

```json
{
  "publication_id": "review_film_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://reviewfilmreview.wordpress.com",
  "allowed_url_prefixes": [
    "https://reviewfilmreview.wordpress.com/20"
  ],
  "review_url_keywords": [
    "/20"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.entry-title",
      "meta[property='og:title']::attr(content)",
      "h1"
    ],
    "published_at_selectors": [
      "time.entry-date.published::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "meta[itemprop='ratingValue']::attr(content)",
      ".rating",
      "[class*='rating']"
    ],
    "critic_name_selectors": [
      "span.author.vcard a",
      "span.author.vcard",
      "a.url.fn"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Refined for Review Film Review's WordPress date-based article paths to avoid archive, tag, and share-link noise from the broad domain-level stub.",
  "sample_url": "https://reviewfilmreview.wordpress.com/2026/04/20/mother-mary-2026/",
  "observed": {
    "title_tag": "Thoughts on Mother Mary (2026) – Review Film Review",
    "h1_text": "Thoughts on Mother Mary (2026)",
    "canonical_link": "https://reviewfilmreview.wordpress.com/2026/04/20/mother-mary-2026/"
  }
}
```

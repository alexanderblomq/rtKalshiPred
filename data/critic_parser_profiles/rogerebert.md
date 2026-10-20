# Parser Profile: rogerebert

Review and refine the JSON block below.

```json
{
  "publication_id": "rogerebert",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.rogerebert.com/reviews",
  "allowed_url_prefixes": [
    "https://www.rogerebert.com/reviews/"
  ],
  "review_url_keywords": [
    "/reviews/"
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
  "notes": "Stub generated for RogerEbert.com with sample_url=None. Refine selectors after inspection."
}
```

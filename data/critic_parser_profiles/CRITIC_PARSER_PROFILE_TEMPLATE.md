# Critic Parser Profile Template

Use this document format when an AI or human inspects a critic or outlet website and wants to turn that inspection into scraper configuration.

Instructions:
- Fill the JSON block only.
- Keep selectors narrow and stable.
- Prefer outlet-level selectors over article-specific selectors.
- Use CSS selectors.
- Use `::attr(name)` when the value is in an attribute.
- Leave fields empty when unknown.

```json
{
  "publication_id": "example_publication",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://example.com/reviews",
  "allowed_url_prefixes": [
    "https://example.com/reviews/"
  ],
  "review_url_keywords": [
    "review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article p",
      ".article-body p"
    ],
    "score_selectors": [
      ".rating",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "meta[name='author']::attr(content)",
      ".author-name"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)"
    ]
  },
  "notes": "Generated from manual or AI inspection of the publication site."
}
```

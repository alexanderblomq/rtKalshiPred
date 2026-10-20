# Parser Profile: reality_blurred

Review and refine the JSON block below.

```json
{
  "publication_id": "reality_blurred",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.realityblurred.com",
  "allowed_url_prefixes": [
    "https://www.realityblurred.com/realitytv/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1[itemprop='headline'].entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div[itemprop='text'].entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a.author-avatar-link",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Reality Blurred with sample_url='https://www.realityblurred.com/realitytv/2024/06/queer-planet-peacock-review/'. Refine selectors after inspection.",
  "sample_url": "https://www.realityblurred.com/realitytv/2024/06/queer-planet-peacock-review/",
  "observed": {
    "title_tag": "Queer Planet: a nature doc that has a gay old anthropomorphizing time \u2013 reality blurred",
    "h1_text": "Queer Planet: a nature doc that has a gay old anthropomorphizing time",
    "canonical_link": "https://www.realityblurred.com/realitytv/2024/06/queer-planet-peacock-review/"
  }
}
```

# Parser Profile: geek_vibes_nation

Review and refine the JSON block below.

```json
{
  "publication_id": "geek_vibes_nation",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://geekvibesnation.com",
  "allowed_url_prefixes": [
    "https://geekvibesnation.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.elementor-heading-title.elementor-size-default",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "div.elementor-element.elementor-element-73b122e9 p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "span.number.rating",
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
  "notes": "Stub generated for Geek Vibes Nation with sample_url='https://geekvibesnation.com/the-travel-companion-review/'. Refine selectors after inspection.",
  "sample_url": "https://geekvibesnation.com/the-travel-companion-review/",
  "observed": {
    "title_tag": "'The Travel Companion' Review - A Directionless Comedy Without Laughter Or Thought",
    "h1_text": "\u2018The Travel Companion\u2019 Review \u2013 A Directionless Comedy Without Laughter Or Thought",
    "canonical_link": "https://geekvibesnation.com/the-travel-companion-review/"
  }
}
```

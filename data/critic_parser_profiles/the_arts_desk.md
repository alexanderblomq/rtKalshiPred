# Parser Profile: the_arts_desk

Review and refine the JSON block below.

```json
{
  "publication_id": "the_arts_desk",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.theartsdesk.com",
  "allowed_url_prefixes": [
    "https://www.theartsdesk.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.articleTitle",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article.node.node--type-article p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div.block.block-tad-common",
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
  "notes": "Stub generated for The Arts Desk with sample_url='https://www.theartsdesk.com/film/blue-trail-review-take-it-river'. Refine selectors after inspection.",
  "sample_url": "https://www.theartsdesk.com/film/blue-trail-review-take-it-river",
  "observed": {
    "title_tag": "The Blue Trail review - take it to the river | The Arts Desk",
    "h1_text": "The Blue Trail review - take it to the river",
    "canonical_link": "http://www.theartsdesk.com/film/blue-trail-review-take-it-river"
  }
}
```

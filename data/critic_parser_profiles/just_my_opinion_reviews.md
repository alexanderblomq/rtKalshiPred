# Parser Profile: just_my_opinion_reviews

Review and refine the JSON block below.

```json
{
  "publication_id": "just_my_opinion_reviews",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.justmyopinion.net",
  "allowed_url_prefixes": [
    "https://www.justmyopinion.net"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.screen-reader-text.site_logo",
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
      "div.entry-content.blog_post_text p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div.my_rating",
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a.meta_author_avatar_url",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Just My Opinion Reviews with sample_url='https://www.justmyopinion.net/you-me-tuscany-review/'. Refine selectors after inspection.",
  "sample_url": "https://www.justmyopinion.net/you-me-tuscany-review/",
  "observed": {
    "title_tag": "YOU, ME & TUSCANY Review - Just My Opinion Reviews",
    "h1_text": "Just My Opinion Reviews",
    "canonical_link": "https://www.justmyopinion.net/you-me-tuscany-review/"
  }
}
```

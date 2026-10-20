# Parser Profile: pajiba

Review and refine the JSON block below.

```json
{
  "publication_id": "pajiba",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.pajiba.com/film_reviews/",
  "allowed_url_prefixes": [
    "https://www.pajiba.com/film_reviews/"
  ],
  "review_url_keywords": [
    "/film_reviews/review-"
  ],
  "selectors": {
    "headline_selectors": [
      "meta[property='og:title']::attr(content)",
      "h1",
      "title"
    ],
    "published_at_selectors": [
      "time::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "article p",
      "main p"
    ],
    "score_selectors": [
      "meta[itemprop='ratingValue']::attr(content)",
      ".rating",
      "[class*='rating']"
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
  "notes": "Refined for Pajiba's film review archive and article URL pattern so the crawler targets review articles under /film_reviews/ instead of the broader site front page.",
  "sample_url": "https://www.pajiba.com/film_reviews/review-roommates-is-a-surprisingly-solid-happy-madison-comedy.php",
  "observed": {
    "title_tag": "Review: 'Roommates' Is a Surprisingly Solid Happy Madison Comedy",
    "canonical_link": "https://www.pajiba.com/film_reviews/review-roommates-is-a-surprisingly-solid-happy-madison-comedy.php"
  }
}
```

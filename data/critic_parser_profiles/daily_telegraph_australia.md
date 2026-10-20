# Parser Profile: daily_telegraph_australia

Review and refine the JSON block below.

```json
{
  "publication_id": "daily_telegraph_australia",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.dailytelegraph.com.au",
  "allowed_url_prefixes": [
    "https://www.dailytelegraph.com.au/entertainment/"
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
  "notes": "Stub generated for Daily Telegraph (Australia) with sample_url='https://www.dailytelegraph.com.au/entertainment/fuze-review-worthingtons-underrated-talent-on-display-in-frenetic-new-thriller/news-story/dcfe27697e1082e677c92d434c7e7498'. Refine selectors after inspection.",
  "sample_url": "https://www.dailytelegraph.com.au/entertainment/fuze-review-worthingtons-underrated-talent-on-display-in-frenetic-new-thriller/news-story/dcfe27697e1082e677c92d434c7e7498",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

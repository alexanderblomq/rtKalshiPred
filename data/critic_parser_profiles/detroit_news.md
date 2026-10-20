# Parser Profile: detroit_news

Review and refine the JSON block below.

```json
{
  "publication_id": "detroit_news",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.detroitnews.com",
  "allowed_url_prefixes": [
    "https://www.detroitnews.com/story/entertainment/movies/"
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
  "notes": "Stub generated for Detroit News with sample_url='https://www.detroitnews.com/story/entertainment/movies/2026/04/21/michael-cuts-corners-but-brings-king-of-pop-back-to-life-our-review/89712231007/'. Refine selectors after inspection.",
  "sample_url": "https://www.detroitnews.com/story/entertainment/movies/2026/04/21/michael-cuts-corners-but-brings-king-of-pop-back-to-life-our-review/89712231007/",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

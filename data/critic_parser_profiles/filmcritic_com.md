# Parser Profile: filmcritic_com

Review and refine the JSON block below.

```json
{
  "publication_id": "filmcritic_com",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://medium.com",
  "allowed_url_prefixes": [
    "https://medium.com/eyes-wide-open/"
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
  "notes": "Stub generated for Filmcritic.com with sample_url='https://medium.com/eyes-wide-open/going-clear-everything-about-scientology-and-tom-cruise-you-never-wanted-to-know-3e0df8188767#.e03x87kn1'. Refine selectors after inspection.",
  "sample_url": "https://medium.com/eyes-wide-open/going-clear-everything-about-scientology-and-tom-cruise-you-never-wanted-to-know-3e0df8188767#.e03x87kn1",
  "observed_error": "HTTPError: HTTP Error 403: Forbidden"
}
```

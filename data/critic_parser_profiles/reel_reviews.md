# Parser Profile: reel_reviews

Review and refine the JSON block below.

```json
{
  "publication_id": "reel_reviews",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.reelreviews.com",
  "allowed_url_prefixes": [
    "https://www.reelreviews.com"
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
      "time[itemprop='datePublished']::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div[itemprop='articleBody'].article-body p",
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
      "meta[name='author']",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Reel Reviews with sample_url='https://www.reelreviews.com/intheaters/normal-movie-review'. Refine selectors after inspection.",
  "sample_url": "https://www.reelreviews.com/intheaters/normal-movie-review",
  "observed": {
    "title_tag": "Normal (2026): In a Town Called Normal, Nothing is What it Seems - Movie Review",
    "h1_text": "In Theaters and Digital",
    "canonical_link": null
  }
}
```

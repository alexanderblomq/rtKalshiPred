# Parser Profile: anime_news_network

Review and refine the JSON block below.

```json
{
  "publication_id": "anime_news_network",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.animenewsnetwork.com",
  "allowed_url_prefixes": [
    "https://www.animenewsnetwork.com/review/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1#page_header.same-width-as-main",
      "h1",
      "meta[property='og:title']::attr(content)"
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
  "notes": "Stub generated for Anime News Network with sample_url='https://www.animenewsnetwork.com/review/zombie-land-saga/yumeginga-paradise/film/.233283'. Refine selectors after inspection.",
  "sample_url": "https://www.animenewsnetwork.com/review/zombie-land-saga/yumeginga-paradise/film/.233283",
  "observed": {
    "title_tag": "Zombie Land Saga: Yumeginga Paradise Film Review - Review - Anime News Network",
    "h1_text": "Review",
    "canonical_link": "https://www.animenewsnetwork.com/review/zombie-land-saga/yumeginga-paradise/film/.233283"
  }
}
```

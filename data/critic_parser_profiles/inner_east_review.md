# Parser Profile: inner_east_review

Review and refine the JSON block below.

```json
{
  "publication_id": "inner_east_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.innereastreview.com.au",
  "allowed_url_prefixes": [
    "https://www.innereastreview.com.au/story/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.mb-5.text-heading-mobile",
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
  "notes": "Stub generated for Inner East Review with sample_url='https://www.innereastreview.com.au/story/9225319/lee-cronins-the-mummy-review-a-frighteningly-fresh-reboot/'. Refine selectors after inspection.",
  "sample_url": "https://www.innereastreview.com.au/story/9225319/lee-cronins-the-mummy-review-a-frighteningly-fresh-reboot/",
  "observed": {
    "title_tag": "Lee Cronin's The Mummy review: A frighteningly fresh reboot | Inner East Review | Melbourne, Victoria",
    "h1_text": "Forget Fraser, this Mummy is a different, more terrifying, beast",
    "canonical_link": "https://www.canberratimes.com.au/story/9225319/lee-cronins-the-mummy-review-a-frighteningly-fresh-reboot/"
  }
}
```

# Parser Profile: broad_street_review

Review and refine the JSON block below.

```json
{
  "publication_id": "broad_street_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.broadstreetreview.com",
  "allowed_url_prefixes": [
    "https://www.broadstreetreview.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.text-4xl.font-extrabold",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "time::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "main p",
      "article p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "link[rel='author']",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Broad Street Review with sample_url='https://www.broadstreetreview.com/reviews/philadelphia-jewish-film-and-media-festival-presents-lost-cause-all-gods-children-and-fantasy-life'. Refine selectors after inspection.",
  "sample_url": "https://www.broadstreetreview.com/reviews/philadelphia-jewish-film-and-media-festival-presents-lost-cause-all-gods-children-and-fantasy-life",
  "observed": {
    "title_tag": "Philadelphia Jewish Film and Media Festival\u2026 | Broad Street Review",
    "h1_text": "Philadelphia Jewish Film and Media Festival presents Lost Cause , All God\u2019s Children , and Fantasy Life",
    "canonical_link": "https://www.broadstreetreview.com/reviews/philadelphia-jewish-film-and-media-festival-presents-lost-cause-all-gods-children-and-fantasy-life"
  }
}
```

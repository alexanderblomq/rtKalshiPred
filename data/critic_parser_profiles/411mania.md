# Parser Profile: 411mania

Review and refine the JSON block below.

```json
{
  "publication_id": "411mania",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://411mania.com/movies/",
  "allowed_url_prefixes": [
    "https://411mania.com/movies/"
  ],
  "review_url_keywords": [
    "-review/"
  ],
  "selectors": {
    "headline_selectors": [
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div[class*='scores__overview-number--'] span",
      "div.scores__overview--number span"
    ],
    "critic_name_selectors": [
      "span.author.name",
      "[class*='author'] a",
      "[class*='author']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Added a dedicated 411mania profile so score extraction can use the article score box instead of relying only on generic text heuristics.",
  "sample_url": "https://411mania.com/movies/overlook-2026-buffet-infinity-review/",
  "observed": {
    "title_tag": "Overlook 2026: Buffet Infinity Review",
    "h1_text": "Overlook 2026: Buffet Infinity Review",
    "canonical_link": "https://411mania.com/movies/overlook-2026-buffet-infinity-review/"
  }
}
```

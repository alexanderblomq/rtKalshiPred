# Parser Profile: black_nerd_problems

Review and refine the JSON block below.

```json
{
  "publication_id": "black_nerd_problems",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://blacknerdproblems.com",
  "allowed_url_prefixes": [
    "https://blacknerdproblems.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.entry-content p",
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
  "notes": "Stub generated for Black Nerd Problems with sample_url='https://blacknerdproblems.com/jay-jurden-yes-maam-review/'. Refine selectors after inspection.",
  "sample_url": "https://blacknerdproblems.com/jay-jurden-yes-maam-review/",
  "observed": {
    "title_tag": "Jay Jurden's 'Yes Ma'am' Comedy Special is Buzzer Beater Smooth - Black Nerd Problems",
    "h1_text": "Jay Jurden\u2019s \u2018Yes Ma\u2019am\u2019 Comedy Special is Buzzer Beater Smooth",
    "canonical_link": "https://blacknerdproblems.com/jay-jurden-yes-maam-review/"
  }
}
```

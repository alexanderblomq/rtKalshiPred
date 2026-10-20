# Parser Profile: critic_s_notebook

Review and refine the JSON block below.

```json
{
  "publication_id": "critic_s_notebook",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.criticsnotebook.com",
  "allowed_url_prefixes": [
    "https://www.criticsnotebook.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1#banner-header",
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
  "notes": "Stub generated for Critic's Notebook with sample_url='https://www.criticsnotebook.com/chasing-summer-movie-review-josephine-decker-iliza-shlesinger-sundance-film-festival/'. Refine selectors after inspection.",
  "sample_url": "https://www.criticsnotebook.com/chasing-summer-movie-review-josephine-decker-iliza-shlesinger-sundance-film-festival/",
  "observed": {
    "title_tag": "'Chasing Summer' Review: You Can Go Home Again",
    "h1_text": "Critic's Notebook",
    "canonical_link": "https://www.criticsnotebook.com/"
  }
}
```

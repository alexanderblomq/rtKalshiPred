# Parser Profile: australian_book_review

Review and refine the JSON block below.

```json
{
  "publication_id": "australian_book_review",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.australianbookreview.com.au/arts-update",
  "allowed_url_prefixes": [
    "https://www.australianbookreview.com.au/arts-update/"
  ],
  "review_url_keywords": [
    "/arts-update/"
  ],
  "selectors": {
    "headline_selectors": [
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "main p",
      "article p"
    ],
    "score_selectors": [
      "meta[itemprop='ratingValue']::attr(content)",
      ".rating",
      "[class*='rating']"
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
  "notes": "Refined for Australian Book Review's arts-update article paths so discovery does not treat the whole magazine navigation and book-review taxonomy as film-review candidates.",
  "sample_url": "https://www.australianbookreview.com.au/arts-update/101-arts-update/14873-wuthering-heights-fennell-s-sticky-pseudo-adaptation-of-emily-bronte-s-novel",
  "observed": {
    "title_tag": "‘\"Wuthering Heights\": Fennell’s adaptation of that Emily Brontë novel’ by Phillippa Hawker",
    "canonical_link": "https://www.australianbookreview.com.au/arts-update/101-arts-update/14873-wuthering-heights-fennell-s-sticky-pseudo-adaptation-of-emily-bronte-s-novel"
  }
}
```

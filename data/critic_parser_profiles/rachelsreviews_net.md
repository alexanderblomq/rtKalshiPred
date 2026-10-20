# Parser Profile: rachelsreviews_net

Review and refine the JSON block below.

```json
{
  "publication_id": "rachelsreviews_net",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://rachelsreviews.net",
  "allowed_url_prefixes": [
    "https://rachelsreviews.net/20"
  ],
  "review_url_keywords": [
    "/20"
  ],
  "selectors": {
    "headline_selectors": [
      "meta[property='og:title']::attr(content)",
      "article h1",
      "h1.entry-title"
    ],
    "published_at_selectors": [
      "time.entry-date.published::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div.entry-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "meta[itemprop='ratingValue']::attr(content)",
      ".rating",
      "[class*='rating']"
    ],
    "critic_name_selectors": [
      "span.author.vcard a",
      "span.author.vcard",
      "a.url.fn"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Refined for rachelsreviews.net's date-based WordPress permalinks and corrected the headline selectors so the parser does not capture the site title banner as the article headline.",
  "sample_url": "https://rachelsreviews.net/2026/04/01/can-a-movie-win-me-over-on-cuteness-vibes-yes-the-super-mario-galaxy-movie-review/",
  "observed": {
    "title_tag": "Can a movie win me over on cuteness vibes? Yes ‘The Super Mario Galaxy Movie’ (Review)",
    "canonical_link": "https://rachelsreviews.net/2026/04/01/can-a-movie-win-me-over-on-cuteness-vibes-yes-the-super-mario-galaxy-movie-review/"
  }
}
```

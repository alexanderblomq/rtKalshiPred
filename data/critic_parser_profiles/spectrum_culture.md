# Parser Profile: spectrum_culture

Review and refine the JSON block below.

```json
{
  "publication_id": "spectrum_culture",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://spectrumculture.com",
  "allowed_url_prefixes": [
    "https://spectrumculture.com/2026/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.post-title.entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article#post-117754.hentry.post-117754 p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "span.star-rating",
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
  "notes": "Stub generated for Spectrum Culture with sample_url='https://spectrumculture.com/2026/04/20/marama-review/'. Refine selectors after inspection.",
  "sample_url": "https://spectrumculture.com/2026/04/20/marama-review/",
  "observed": {
    "title_tag": "M\u0101rama - Spectrum Culture",
    "h1_text": "M\u0101rama",
    "canonical_link": "https://spectrumculture.com/2026/04/20/marama-review/"
  }
}
```

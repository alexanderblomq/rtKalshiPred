# Parser Profile: beyond_the_cinerama_dome

Review and refine the JSON block below.

```json
{
  "publication_id": "beyond_the_cinerama_dome",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://beyondthecineramadome.com",
  "allowed_url_prefixes": [
    "https://beyondthecineramadome.com/movie-reviews/"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1[itemprop='headline'].entry-title.entry-title--large",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "time.dt-published.blog-meta-item::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "article#sections.sections p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "meta[itemprop='author']",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Beyond the Cinerama Dome with sample_url='https://beyondthecineramadome.com/movie-reviews/michael-review'. Refine selectors after inspection.",
  "sample_url": "https://beyondthecineramadome.com/movie-reviews/michael-review",
  "observed": {
    "title_tag": "\u201cMichael\u201d Misses a Note \u2014 Beyond the Cinerama Dome",
    "h1_text": "\u201cMichael\u201d Misses a Note",
    "canonical_link": "https://beyondthecineramadome.com/movie-reviews/michael-review"
  }
}
```

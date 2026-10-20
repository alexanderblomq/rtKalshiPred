# Parser Profile: movies_we_texted_about

Review and refine the JSON block below.

```json
{
  "publication_id": "movies_we_texted_about",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://movieswetextedabout.com",
  "allowed_url_prefixes": [
    "https://movieswetextedabout.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1[itemprop='headline'].entry-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time[itemprop='dateModified'].updated::attr(datetime)",
      "meta[name='parsely-pub-date']::attr(content)",
      "time::attr(datetime)"
    ],
    "body_selectors": [
      "div[itemprop='text'].entry-content p",
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
      "meta[name='author']",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for Movies We Texted About with sample_url='https://movieswetextedabout.com/seized-is-the-moment-sundance-2026-film-review/#more-4531'. Refine selectors after inspection.",
  "sample_url": "https://movieswetextedabout.com/seized-is-the-moment-sundance-2026-film-review/#more-4531",
  "observed": {
    "title_tag": "'Seized' is The Moment (Sundance 2026 Film Review) -",
    "h1_text": "\u2018Seized\u2019 is The Moment (Sundance 2026 Film Review)",
    "canonical_link": "https://movieswetextedabout.com/seized-is-the-moment-sundance-2026-film-review/"
  }
}
```

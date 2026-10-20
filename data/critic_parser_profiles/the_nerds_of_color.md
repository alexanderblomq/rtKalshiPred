# Parser Profile: the_nerds_of_color

Review and refine the JSON block below.

```json
{
  "publication_id": "the_nerds_of_color",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://thenerdsofcolor.org",
  "allowed_url_prefixes": [
    "https://thenerdsofcolor.org"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.site-title",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "meta[property='article:published_time']::attr(content)",
      "time.entry-date.published::attr(datetime)",
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
      "h3.author-name",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for The Nerds of Color with sample_url='https://thenerdsofcolor.org/2026/03/26/the-ai-doc-or-how-i-became-an-apocaloptimist-is-a-rousing-call-for-humanity-to-take-action/'. Refine selectors after inspection.",
  "sample_url": "https://thenerdsofcolor.org/2026/03/26/the-ai-doc-or-how-i-became-an-apocaloptimist-is-a-rousing-call-for-humanity-to-take-action/",
  "observed": {
    "title_tag": "\u2018The AI Doc: Or How I Became an Apocaloptimist\u2019 is a Rousing Call for Humanity to Take Action \u2013 The Nerds of Color",
    "h1_text": "The Nerds of Color",
    "canonical_link": "https://thenerdsofcolor.org/2026/03/26/the-ai-doc-or-how-i-became-an-apocaloptimist-is-a-rousing-call-for-humanity-to-take-action/"
  }
}
```

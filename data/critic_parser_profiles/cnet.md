# Parser Profile: cnet

Review and refine the JSON block below.

```json
{
  "publication_id": "cnet",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://www.cnet.com",
  "allowed_url_prefixes": [
    "https://www.cnet.com"
  ],
  "review_url_keywords": [
    "review",
    "reviews",
    "film-review",
    "movie-review"
  ],
  "selectors": {
    "headline_selectors": [
      "h1.c-contentHeader_headline.u-speakableText",
      "h1",
      "meta[property='og:title']::attr(content)"
    ],
    "published_at_selectors": [
      "time::attr(datetime)",
      "meta[property='article:published_time']::attr(content)",
      "meta[name='parsely-pub-date']::attr(content)"
    ],
    "body_selectors": [
      "article.c-ShortcodeContent.c-ShortcodeContent-theme:default p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      ".rating",
      "[class*='rating']",
      "meta[itemprop='ratingValue']::attr(content)"
    ],
    "critic_name_selectors": [
      "a[rel='author'].c-globalAuthorCard_link.u-flexbox-alignSelfCenter",
      "meta[name='author']::attr(content)",
      "[class*='author'] a",
      "[class*='author-name']"
    ],
    "canonical_url_selectors": [
      "link[rel='canonical']::attr(href)",
      "meta[property='og:url']::attr(content)"
    ]
  },
  "notes": "Stub generated for CNET with sample_url='https://www.cnet.com/tech/services-and-software/mike-and-nick-and-nick-and-alice-hulu/'. Refine selectors after inspection.",
  "sample_url": "https://www.cnet.com/tech/services-and-software/mike-and-nick-and-nick-and-alice-hulu/",
  "observed": {
    "title_tag": "Hulu's New Crime Caper Comedy Is a Raucous Shoot 'Em Up Throwback - CNET",
    "h1_text": "Hulu's New Crime Caper Comedy Is a Raucous Shoot 'Em Up Throwback",
    "canonical_link": "https://www.cnet.com/tech/services-and-software/mike-and-nick-and-nick-and-alice-hulu/"
  }
}
```

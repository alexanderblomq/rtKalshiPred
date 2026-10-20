# Parser Profile: review_nation

Review and refine the JSON block below.

```json
{
  "publication_id": "review_nation",
  "source_type": "article",
  "adapter": "article",
  "discovery_url": "https://reviewnation.net",
  "allowed_url_prefixes": [
    "https://reviewnation.net"
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
      "article#the-post.container-wrapper.post-content p",
      "article p",
      "main p"
    ],
    "score_selectors": [
      "div.review-final-score",
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
  "notes": "Stub generated for Review Nation with sample_url='https://reviewnation.net/review-song-sung-blue-jackman-hudson-make-beautiful-music-together/'. Refine selectors after inspection.",
  "sample_url": "https://reviewnation.net/review-song-sung-blue-jackman-hudson-make-beautiful-music-together/",
  "observed": {
    "title_tag": "Review: Song Sung Blue \"Jackman & Hudson make beautiful music together\" - Review Nation",
    "h1_text": "Review: Song Sung Blue \u201cJackman & Hudson make beautiful music together\u201d",
    "canonical_link": "https://reviewnation.net/review-song-sung-blue-jackman-hudson-make-beautiful-music-together/"
  }
}
```

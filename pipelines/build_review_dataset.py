from __future__ import annotations

import argparse
import json
from json import JSONDecoder
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import Request, urlopen

from pipelines.enrich_publications import sort_publications_by_value
from scrapers.review_scraper import scrape_review


RT_BASE_URL = "https://www.rottentomatoes.com"


def _load_json(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "rtKalshiPred/0.1"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_review_objects(html: str) -> List[Dict[str, object]]:
    decoder = JSONDecoder()
    results: List[Dict[str, object]] = []
    needle = '{"authorId"'
    start = 0

    while True:
        idx = html.find(needle, start)
        if idx == -1:
            break
        try:
            obj, end = decoder.raw_decode(html[idx:])
        except json.JSONDecodeError:
            start = idx + len(needle)
            continue
        start = idx + end
        if isinstance(obj, dict) and "publicationReviewUrl" in obj and "scoreSentiment" in obj:
            results.append(obj)

    deduped: Dict[str, Dict[str, object]] = {}
    for obj in results:
        deduped[obj["publicationReviewUrl"]] = obj
    return list(deduped.values())


def build_row(publication: Dict[str, object], review_obj: Dict[str, object], include_article_scrape: bool) -> Dict[str, object]:
    url = review_obj.get("publicationReviewUrl")
    row = {
        "publication_id": publication["publication_id"],
        "outlet_name": publication["outlet_name"],
        "critic_name": review_obj.get("authorName"),
        "review_url": url,
        "media_title": review_obj.get("mediaTitle"),
        "media_info": review_obj.get("mediaInfo"),
        "rt_score_sentiment": review_obj.get("scoreSentiment"),
        "fresh_label": 1 if review_obj.get("scoreSentiment") == "POSITIVE" else 0,
        "original_score": review_obj.get("originalScore"),
        "rt_quote": review_obj.get("quote"),
        "rt_review_date": review_obj.get("date"),
        "headline": None,
        "published_at": None,
        "body_text": None,
        "scrape_succeeded": False,
    }

    if not include_article_scrape or not url:
        return row

    try:
        scraped = scrape_review(url, publication["publication_id"], include_disabled=True)
    except Exception:
        return row

    row["headline"] = scraped.get("headline")
    row["published_at"] = scraped.get("published_at")
    row["body_text"] = scraped.get("body_text")
    row["scrape_succeeded"] = True
    return row


def select_publications(
    publications: List[Dict[str, object]],
    publication_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    approved_only: bool = False,
) -> List[Dict[str, object]]:
    selected = publications
    if approved_only:
        selected = [publication for publication in selected if publication.get("approved_publication")]
    if publication_ids:
        wanted = set(publication_ids)
        selected = [publication for publication in selected if publication["publication_id"] in wanted]
    selected = sort_publications_by_value(selected)
    if limit is not None:
        selected = selected[:limit]
    return selected


def run(
    publication_registry_path: str = "data/critics/publication_registry.json",
    output_path: str = "data/processed/review_training_dataset.jsonl",
    publication_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    approved_only: bool = False,
    include_article_scrape: bool = True,
) -> None:
    publications = _load_json(Path(publication_registry_path))
    selected = select_publications(
        publications,
        publication_ids=publication_ids,
        limit=limit,
        approved_only=approved_only,
    )

    output_rows: List[Dict[str, object]] = []
    for publication in selected:
        rt_source_path = publication.get("rt_source_path")
        if not rt_source_path:
            continue
        url = rt_source_path if str(rt_source_path).startswith("http") else RT_BASE_URL + str(rt_source_path)
        try:
            html = fetch_html(url)
        except Exception:
            continue

        for review_obj in extract_review_objects(html):
            output_rows.append(build_row(publication, review_obj, include_article_scrape=include_article_scrape))

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        for row in output_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Saved {len(output_rows)} review rows to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build an RT-labeled review dataset from publication source pages.")
    parser.add_argument("--publication-registry", default="data/critics/publication_registry.json")
    parser.add_argument("--output", default="data/processed/review_training_dataset.jsonl")
    parser.add_argument("--publication-id", action="append", dest="publication_ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--approved-only", action="store_true")
    parser.add_argument("--skip-article-scrape", action="store_true")
    args = parser.parse_args()

    run(
        publication_registry_path=args.publication_registry,
        output_path=args.output,
        publication_ids=args.publication_ids,
        limit=args.limit,
        approved_only=args.approved_only,
        include_article_scrape=not args.skip_article_scrape,
    )

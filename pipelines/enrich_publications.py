from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pipelines.publication_source_inference import infer_publication_source_type


RT_BASE_URL = "https://www.rottentomatoes.com"
EXCLUDED_DOMINANT_HOSTS = {
    "www.newspapers.com",
    "newspapers.com",
    "web.archive.org",
}


def _load_json(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "rtKalshiPred/0.1"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_publication_review_urls(html: str) -> List[str]:
    matches = re.findall(r'publicationReviewUrl":"(https:[^"]+)"', html)
    return list(dict.fromkeys(matches))


def normalize_base_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def extract_effective_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc == "web.archive.org":
        match = re.search(r"(https?://.+)$", parsed.path)
        if match:
            return match.group(1)
    return url


def infer_path_prefix(urls: List[str]) -> Optional[str]:
    effective_urls = [extract_effective_url(url) for url in urls]
    unique_urls = list(dict.fromkeys(effective_urls))
    paths = [urlparse(url).path.strip("/") for url in unique_urls if urlparse(url).path.strip("/")]
    unique_paths = list(dict.fromkeys(paths))
    if len(unique_paths) < 2:
        return None

    path_segments: List[List[str]] = [path.split("/") for path in unique_paths]

    if not path_segments:
        return None

    prefix: List[str] = []
    for segment_group in zip(*path_segments):
        if len(set(segment_group)) != 1:
            break
        prefix.append(segment_group[0])

    if not prefix:
        return None
    return "/" + "/".join(prefix) + "/"


def infer_enrichment(review_urls: List[str]) -> Dict[str, object]:
    if not review_urls:
        return {
            "site_base_url": None,
            "sample_review_urls": [],
            "review_url_count": 0,
            "dominant_host": None,
            "inferred_review_path_prefix": None,
        }

    effective_urls = [extract_effective_url(url) for url in review_urls]
    hosts = Counter(
        urlparse(url).netloc
        for url in effective_urls
        if urlparse(url).netloc not in EXCLUDED_DOMINANT_HOSTS
    )
    if not hosts:
        return {
            "site_base_url": None,
            "sample_review_urls": review_urls[:5],
            "review_url_count": len(review_urls),
            "dominant_host": None,
            "inferred_review_path_prefix": None,
        }

    dominant_host, _ = hosts.most_common(1)[0]
    dominant_urls = [url for url in effective_urls if urlparse(url).netloc == dominant_host]
    site_base_url = normalize_base_url(dominant_urls[0])

    return {
        "site_base_url": site_base_url,
        "sample_review_urls": dominant_urls[:5],
        "review_url_count": len(review_urls),
        "dominant_host": dominant_host,
        "inferred_review_path_prefix": infer_path_prefix(dominant_urls),
    }


def enrich_publication(publication: Dict[str, object]) -> Dict[str, object]:
    rt_source_path = publication.get("rt_source_path")
    if not rt_source_path:
        return dict(publication)

    url = rt_source_path if str(rt_source_path).startswith("http") else RT_BASE_URL + str(rt_source_path)
    html = fetch_html(url)
    review_urls = extract_publication_review_urls(html)
    enrichment = infer_enrichment(review_urls)

    enriched = dict(publication)
    existing_base_url = str(enriched.get("site_base_url") or "")
    existing_host = urlparse(existing_base_url).netloc if existing_base_url else None
    if enrichment["site_base_url"] and (not existing_base_url or existing_host in EXCLUDED_DOMINANT_HOSTS):
        enriched["site_base_url"] = enrichment["site_base_url"]
    if existing_host in EXCLUDED_DOMINANT_HOSTS and not enrichment["site_base_url"]:
        enriched["site_base_url"] = None
    enriched["sample_review_urls"] = enrichment["sample_review_urls"]
    enriched["review_url_count"] = enrichment["review_url_count"]
    enriched["dominant_host"] = enrichment["dominant_host"]
    enriched["inferred_review_path_prefix"] = enrichment["inferred_review_path_prefix"]
    enriched.pop("enrichment_error", None)
    return enriched


def enrich_publications(publications: List[Dict[str, object]], max_workers: int = 10) -> Tuple[List[Dict[str, object]], int]:
    enriched: Dict[str, Dict[str, object]] = {}
    enriched_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(enrich_publication, publication): publication
            for publication in publications
        }
        for future in as_completed(future_map):
            publication = future_map[future]
            publication_id = publication["publication_id"]
            try:
                result = future.result()
            except Exception as exc:
                result = dict(publication)
                result["enrichment_error"] = f"{exc.__class__.__name__}: {exc}"
            enriched[publication_id] = result
            if result.get("site_base_url"):
                enriched_count += 1

    ordered = [enriched[publication["publication_id"]] for publication in publications]
    return ordered, enriched_count


def select_publications(
    publications: List[Dict[str, object]],
    publication_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    value_order: bool = False,
    only_missing_base_url: bool = False,
) -> List[Dict[str, object]]:
    selected = publications
    if publication_ids:
        wanted = set(publication_ids)
        selected = [publication for publication in publications if publication["publication_id"] in wanted]
    if only_missing_base_url:
        selected = [publication for publication in selected if not publication.get("site_base_url")]
    if value_order:
        selected = sort_publications_by_value(selected)
    if limit is not None:
        selected = selected[:limit]
    return selected


def publication_value_score(publication: Dict[str, object]) -> Tuple[int, int, int, int, int, int, str]:
    source_type = infer_publication_source_type(publication)
    approved_score = 1 if publication.get("approved_publication") else 0
    critic_count = len(publication.get("critic_names", []))
    enabled_score = 1 if publication.get("enabled") else 0
    article_score = 1 if source_type == "article" else 0
    substack_score = 1 if source_type == "substack" else 0
    unresolved_score = 1 if not publication.get("site_base_url") else 0

    return (
        -unresolved_score,
        -approved_score,
        -enabled_score,
        -article_score,
        -substack_score,
        -critic_count,
        str(publication.get("outlet_name", "")).lower(),
    )


def sort_publications_by_value(publications: List[Dict[str, object]]) -> List[Dict[str, object]]:
    return sorted(publications, key=publication_value_score)


def merge_enriched_subset(
    publications: List[Dict[str, object]],
    enriched_subset: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    by_id = {publication["publication_id"]: dict(publication) for publication in publications}
    for publication in enriched_subset:
        by_id[publication["publication_id"]] = publication
    return [by_id[publication["publication_id"]] for publication in publications]


def run(
    publication_registry_path: str = "data/critics/publication_registry.json",
    max_workers: int = 10,
    publication_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    value_order: bool = False,
    only_missing_base_url: bool = False,
) -> None:
    publication_path = Path(publication_registry_path)
    publications = _load_json(publication_path)
    selected = select_publications(
        publications,
        publication_ids=publication_ids,
        limit=limit,
        value_order=value_order,
        only_missing_base_url=only_missing_base_url,
    )
    enriched_subset, enriched_count = enrich_publications(selected, max_workers=max_workers)
    merged = merge_enriched_subset(publications, enriched_subset)
    publication_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    failed_publications = [publication for publication in enriched_subset if publication.get("enrichment_error")]
    print(f"Saved {len(merged)} publications to {publication_path}")
    print(f"Subset enriched: {len(enriched_subset)}")
    print(f"Subset publications with site_base_url: {enriched_count}")
    print(f"Subset enrichment failures: {len(failed_publications)}")
    for publication in failed_publications[:10]:
        print(f"- {publication['publication_id']}: {publication['enrichment_error']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich publication registry from Rotten Tomatoes source pages.")
    parser.add_argument("--publication-registry", default="data/critics/publication_registry.json")
    parser.add_argument("--max-workers", type=int, default=10)
    parser.add_argument("--publication-id", action="append", dest="publication_ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--value-order", action="store_true")
    parser.add_argument("--only-missing-base-url", action="store_true")
    args = parser.parse_args()

    run(
        args.publication_registry,
        max_workers=args.max_workers,
        publication_ids=args.publication_ids,
        limit=args.limit,
        value_order=args.value_order,
        only_missing_base_url=args.only_missing_base_url,
    )

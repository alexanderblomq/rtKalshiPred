from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


RT_CRITICS_URL = "https://www.rottentomatoes.com/critics/authors"
RT_PUBLICATIONS_URL = "https://www.rottentomatoes.com/critics/sources"
RT_TOP_CRITICS_URL = "https://www.rottentomatoes.com/critics/top_critics"


def build_letter_urls(base_url: str) -> List[str]:
    buckets = ["%23"] + [chr(code) for code in range(ord("a"), ord("z") + 1)]
    return [f"{base_url}?letter={bucket}" for bucket in buckets]


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "rtKalshiPred/0.1"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "unknown"


def parse_publications_html(html: str) -> List[Dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    entries: List[Dict[str, object]] = []

    for item in soup.select('li[data-qa="publication-item"]'):
        link = item.select_one('a[data-qa="publication-item-link"]')
        if link is None:
            continue

        outlet_name = " ".join(link.get_text(" ", strip=True).split())
        badge = item.select_one("rt-badge")
        badge_text = badge.get_text(" ", strip=True) if badge else ""
        href = link.get("href")

        entries.append(
            {
                "publication_id": slugify(outlet_name),
                "outlet_name": outlet_name,
                "approved_publication": "approved publication" in badge_text.lower(),
                "source_type": "article",
                "enabled": False,
                "critic_names": [],
                "site_base_url": None,
                "adapter": "article",
                "rt_source_path": href,
                "rt_badge": badge_text or None,
            }
        )

    return entries


def parse_critics_html(html: str) -> List[Dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    entries: List[Dict[str, object]] = []

    for item in soup.select('li[data-qa="critic-item"]'):
        critic_link = item.select_one('a[data-qa="critic-item-link"]')
        if critic_link is None:
            continue

        critic_name = " ".join(critic_link.get_text(" ", strip=True).split())
        critic_path = critic_link.get("href")
        publication_link = item.select_one('a[data-qa="critic-item-publication-link"]')
        badge = item.select_one("rt-badge")
        badge_text = badge.get_text(" ", strip=True) if badge else ""

        publication_name = None
        publication_path = None
        approval_type = "unknown"

        if badge_text and "individually approved" in badge_text.lower():
            approval_type = "individually_approved"
        elif publication_link is not None:
            publication_name = " ".join(publication_link.get_text(" ", strip=True).split())
            publication_path = publication_link.get("href")
            approval_type = "publication_bound"

        entries.append(
            {
                "critic_id": critic_path.rsplit("/", 1)[-1] if critic_path else slugify(critic_name),
                "critic_name": critic_name,
                "rt_critic_path": critic_path,
                "approval_type": approval_type,
                "publication_name": publication_name,
                "publication_id": slugify(publication_name) if publication_name else None,
                "rt_publication_path": publication_path,
                "top_critic": False,
            }
        )

    return entries


def parse_top_critics_html(html: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    critic_ids: Set[str] = set()

    for item in soup.select('li[data-qa="critic-item"]'):
        critic_link = item.select_one('a[data-qa="critic-item-link"]')
        if critic_link is None:
            continue
        critic_path = critic_link.get("href")
        if critic_path:
            critic_ids.add(critic_path.rsplit("/", 1)[-1])

    return critic_ids


def _load_existing_json(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def merge_publications(existing: List[Dict[str, object]], discovered: List[Dict[str, object]], critics: List[Dict[str, object]]) -> List[Dict[str, object]]:
    existing_by_id = {item["publication_id"]: dict(item) for item in existing}
    critics_by_publication: Dict[str, List[str]] = {}
    for critic in critics:
        publication_id = critic.get("publication_id")
        publication_name = critic.get("publication_name")
        critic_name = critic.get("critic_name")
        if publication_id and publication_name and critic_name:
            critics_by_publication.setdefault(publication_id, []).append(critic_name)

    for item in discovered:
        publication_id = item["publication_id"]
        merged = dict(item)
        if publication_id in existing_by_id:
            current = existing_by_id[publication_id]
            merged["enabled"] = current.get("enabled", merged["enabled"])
            merged["source_type"] = current.get("source_type", merged["source_type"])
            merged["site_base_url"] = current.get("site_base_url", merged["site_base_url"])
            merged["adapter"] = current.get("adapter", merged["adapter"])
            merged["critic_names"] = sorted(set(current.get("critic_names", [])) | set(critics_by_publication.get(publication_id, [])))
        else:
            merged["critic_names"] = sorted(set(critics_by_publication.get(publication_id, [])))
        existing_by_id[publication_id] = merged

    return sorted(existing_by_id.values(), key=lambda item: item["outlet_name"].lower())


def merge_critics(existing: List[Dict[str, object]], discovered: List[Dict[str, object]], top_critic_ids: Set[str]) -> List[Dict[str, object]]:
    existing_by_id = {item["critic_id"]: dict(item) for item in existing}

    for item in discovered:
        critic_id = item["critic_id"]
        merged = dict(existing_by_id.get(critic_id, {}))
        merged.update(item)
        merged["top_critic"] = critic_id in top_critic_ids or bool(merged.get("top_critic"))
        existing_by_id[critic_id] = merged

    return sorted(existing_by_id.values(), key=lambda item: item["critic_name"].lower())


def run(
    publication_registry_path: str = "data/critics/publication_registry.json",
    critic_registry_path: str = "data/critics/critic_registry.json",
) -> None:
    discovered_publications: List[Dict[str, object]] = []
    for url in build_letter_urls(RT_PUBLICATIONS_URL):
        discovered_publications.extend(parse_publications_html(fetch_html(url)))

    discovered_critics: List[Dict[str, object]] = []
    for url in build_letter_urls(RT_CRITICS_URL):
        discovered_critics.extend(parse_critics_html(fetch_html(url)))

    top_critics_html = fetch_html(RT_TOP_CRITICS_URL)
    top_critic_ids = parse_top_critics_html(top_critics_html)

    publication_path = Path(publication_registry_path)
    critic_path = Path(critic_registry_path)
    publication_path.parent.mkdir(parents=True, exist_ok=True)
    critic_path.parent.mkdir(parents=True, exist_ok=True)

    existing_publications = _load_existing_json(publication_path)
    existing_critics = _load_existing_json(critic_path)

    merged_publications = merge_publications(existing_publications, discovered_publications, discovered_critics)
    merged_critics = merge_critics(existing_critics, discovered_critics, top_critic_ids)

    publication_path.write_text(json.dumps(merged_publications, indent=2), encoding="utf-8")
    critic_path.write_text(json.dumps(merged_critics, indent=2), encoding="utf-8")

    print(f"Saved {len(merged_publications)} publications to {publication_path}")
    print(f"Saved {len(merged_critics)} critics to {critic_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Rotten Tomatoes critic/publication registries.")
    parser.add_argument("--publication-registry", default="data/critics/publication_registry.json")
    parser.add_argument("--critic-registry", default="data/critics/critic_registry.json")
    args = parser.parse_args()

    run(args.publication_registry, args.critic_registry)

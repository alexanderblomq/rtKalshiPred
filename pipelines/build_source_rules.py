from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from pipelines.publication_source_inference import infer_publication_adapter, infer_publication_source_type

DEFAULT_REVIEW_KEYWORDS = [
    "review",
    "reviews",
    "film-review",
    "movie-review",
]


def _load_json(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def infer_source_type(publication: Dict[str, object]) -> str:
    return infer_publication_source_type(publication)


def infer_adapter(publication: Dict[str, object]) -> str:
    return infer_publication_adapter(publication)


def build_candidate_rule(publication: Dict[str, object]) -> Dict[str, object]:
    site_base_url = publication.get("site_base_url")
    source_type = infer_source_type(publication)
    adapter = infer_adapter(publication)
    inferred_review_path_prefix = publication.get("inferred_review_path_prefix")

    discovery_url = site_base_url if site_base_url else None
    allowed_url_prefixes = []
    if site_base_url and inferred_review_path_prefix:
        allowed_url_prefixes.append(f"{site_base_url}{inferred_review_path_prefix}")
    elif site_base_url:
        allowed_url_prefixes.append(site_base_url)
    keywords = [] if source_type in {"youtube", "podcast"} else list(DEFAULT_REVIEW_KEYWORDS)

    notes = "Auto-generated placeholder rule."
    if source_type == "youtube":
        notes = "Auto-generated placeholder rule. Requires a future YouTube/channel adapter."
    elif source_type == "podcast":
        notes = "Auto-generated placeholder rule. Requires a future podcast/non-text review adapter."
    elif source_type == "substack":
        notes = "Auto-generated placeholder rule. Substack often works with the shared article path once the base URL is known."
    elif not site_base_url:
        notes = "Auto-generated placeholder rule. Discovery URL and base URL still need enrichment."

    return {
        "publication_id": publication["publication_id"],
        "adapter": adapter,
        "source_type": source_type,
        "discovery_url": discovery_url,
        "allowed_url_prefixes": allowed_url_prefixes,
        "review_url_keywords": keywords,
        "headline_selectors": [],
        "published_at_selectors": [],
        "body_selectors": [],
        "score_selectors": [],
        "canonical_url_selectors": [],
        "generated": True,
        "generation_method": "publication-registry-heuristics-v1",
        "notes": notes,
    }


def merge_rules(publications: List[Dict[str, object]], existing_rules: List[Dict[str, object]]) -> List[Dict[str, object]]:
    existing_by_id = {rule["publication_id"]: dict(rule) for rule in existing_rules}
    merged: List[Dict[str, object]] = []

    for publication in publications:
        publication_id = publication["publication_id"]
        if publication_id in existing_by_id:
            rule = dict(existing_by_id[publication_id])
            if rule.get("generated"):
                merged.append(build_candidate_rule(publication))
                continue

            rule.setdefault("source_type", infer_source_type(publication))
            rule.setdefault("generated", False)
            rule.setdefault("generation_method", None)
            rule.setdefault("notes", None)
            merged.append(rule)
            continue

        merged.append(build_candidate_rule(publication))

    return sorted(merged, key=lambda item: str(item["publication_id"]))


def run(
    publication_registry_path: str = "data/critics/publication_registry.json",
    source_rules_path: str = "data/critics/source_rules.json",
) -> None:
    publication_path = Path(publication_registry_path)
    rules_path = Path(source_rules_path)

    publications = _load_json(publication_path)
    existing_rules = _load_json(rules_path)
    merged_rules = merge_rules(publications, existing_rules)

    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(json.dumps(merged_rules, indent=2), encoding="utf-8")

    print(f"Saved {len(merged_rules)} source rules to {rules_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate source rules for all publication registry entries.")
    parser.add_argument("--publication-registry", default="data/critics/publication_registry.json")
    parser.add_argument("--source-rules", default="data/critics/source_rules.json")
    args = parser.parse_args()

    run(args.publication_registry, args.source_rules)

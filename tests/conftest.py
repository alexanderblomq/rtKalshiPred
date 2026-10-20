import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

@pytest.fixture
def state_store_root():
    root = Path("data/live/test-runs") / f"state-store-{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def registry_paths():
    root = Path("data/test-registry-runs") / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield from _write_registry_fixture(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def registry_root():
    root = Path("data/test-registry-runs") / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _write_registry_fixture(root):
    publications = [
        {
            "publication_id": "rogerebert",
            "outlet_name": "RogerEbert.com",
            "approved_publication": True,
            "source_type": "article",
            "enabled": True,
            "critic_names": ["Roger Ebert"],
            "site_base_url": "https://www.rogerebert.com",
            "adapter": "article",
        },
        {
            "publication_id": "variety",
            "outlet_name": "Variety",
            "approved_publication": True,
            "source_type": "rss",
            "enabled": True,
            "critic_names": ["Owen Gleiberman"],
            "site_base_url": "https://variety.com",
            "adapter": "rss",
        },
        {
            "publication_id": "screendaily",
            "outlet_name": "Screen Daily",
            "approved_publication": True,
            "source_type": "sitemap",
            "enabled": True,
            "critic_names": ["Wendy Ide"],
            "site_base_url": "https://www.screendaily.com",
            "adapter": "sitemap",
        },
    ]
    rules = [
        {
            "publication_id": "rogerebert",
            "adapter": "article",
            "source_type": "article",
            "discovery_url": "https://www.rogerebert.com/reviews",
            "allowed_url_prefixes": ["https://www.rogerebert.com/reviews/"],
            "review_url_keywords": ["review"],
            "headline_selectors": [],
            "published_at_selectors": [],
            "body_selectors": [],
            "score_selectors": [],
            "canonical_url_selectors": [],
        },
        {
            "publication_id": "variety",
            "adapter": "rss",
            "source_type": "rss",
            "discovery_url": "https://variety.com/feed/",
            "allowed_url_prefixes": ["https://variety.com/"],
            "review_url_keywords": ["review"],
            "headline_selectors": [],
            "published_at_selectors": [],
            "body_selectors": [],
            "score_selectors": [],
            "canonical_url_selectors": [],
        },
        {
            "publication_id": "screendaily",
            "adapter": "sitemap",
            "source_type": "sitemap",
            "discovery_url": "https://www.screendaily.com/sitemap.xml",
            "allowed_url_prefixes": ["https://www.screendaily.com/"],
            "review_url_keywords": ["review"],
            "headline_selectors": [],
            "published_at_selectors": [],
            "body_selectors": [],
            "score_selectors": [],
            "canonical_url_selectors": [],
        },
    ]

    publication_registry_path = root / "publication_registry.json"
    source_rules_path = root / "source_rules.json"
    publication_registry_path.write_text(json.dumps(publications), encoding="utf-8")
    source_rules_path.write_text(json.dumps(rules), encoding="utf-8")
    yield publication_registry_path, source_rules_path

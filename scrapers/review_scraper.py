from __future__ import annotations

from typing import Any, Dict, Optional

from scrapers.factory import RegistryView, load_runtime_view


def scrape_review(
    url: str,
    publication_id: str,
    publication_registry_path: str = "data/critics/publication_registry.json",
    source_rules_path: str = "data/critics/source_rules.json",
    include_disabled: bool = False,
    runtime_view: Optional[RegistryView] = None,
) -> Dict[str, Any]:
    """Extract structured review fields from a critic article using the configured scraper."""
    active_runtime_view = runtime_view or load_runtime_view(publication_registry_path, source_rules_path)
    scrapers = active_runtime_view.get_scrapers(include_disabled=include_disabled)

    for scraper in scrapers:
        if scraper.publication.publication_id == publication_id:
            return scraper.scrape(url)

    raise ValueError(f"No configured scraper for publication_id={publication_id!r}")

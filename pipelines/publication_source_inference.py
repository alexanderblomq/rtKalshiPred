from __future__ import annotations

from typing import Dict


SUPPORTED_SOURCE_TYPES = {"article", "substack", "youtube", "podcast"}


def infer_publication_source_type(publication: Dict[str, object]) -> str:
    explicit_source_type = str(publication.get("source_type") or "").strip().lower()
    if explicit_source_type in SUPPORTED_SOURCE_TYPES:
        return explicit_source_type

    outlet_name = str(publication.get("outlet_name", "")).lower()
    site_base_url = str(publication.get("site_base_url") or "").lower()

    if "youtube" in outlet_name or "youtube.com" in site_base_url:
        return "youtube"
    if "podcast" in outlet_name:
        return "podcast"
    if "substack" in outlet_name or ".substack.com" in site_base_url:
        return "substack"
    return "article"


def infer_publication_adapter(publication: Dict[str, object]) -> str:
    explicit_adapter = str(publication.get("adapter") or "").strip().lower()
    if explicit_adapter:
        return explicit_adapter

    source_type = infer_publication_source_type(publication)
    if source_type in {"youtube", "podcast"}:
        return "unsupported"
    return "article"

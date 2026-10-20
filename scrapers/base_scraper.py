from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional
from urllib.request import Request, urlopen


def normalize_critic_names(critic_names: object = None, critic_name: object = None) -> List[str]:
    normalized: List[str] = []

    def _append(values: object) -> None:
        if values is None:
            return
        if isinstance(values, str):
            candidate = values.strip()
            if candidate and candidate not in normalized:
                normalized.append(candidate)
            return
        if isinstance(values, Iterable):
            for value in values:
                if isinstance(value, str):
                    candidate = value.strip()
                    if candidate and candidate not in normalized:
                        normalized.append(candidate)

    _append(critic_names)
    _append(critic_name)
    return normalized


def resolve_primary_critic_name(critic_name: object = None, critic_names: object = None) -> str:
    normalized = normalize_critic_names(critic_names=critic_names, critic_name=critic_name)
    return normalized[0] if normalized else ""


@dataclass
class SourceRule:
    publication_id: str
    adapter: str
    discovery_url: Optional[str] = None
    source_type: Optional[str] = None
    allowed_url_prefixes: List[str] = field(default_factory=list)
    review_url_keywords: List[str] = field(default_factory=list)
    headline_selectors: List[str] = field(default_factory=list)
    published_at_selectors: List[str] = field(default_factory=list)
    body_selectors: List[str] = field(default_factory=list)
    score_selectors: List[str] = field(default_factory=list)
    critic_name_selectors: List[str] = field(default_factory=list)
    canonical_url_selectors: List[str] = field(default_factory=list)
    generated: bool = False
    generation_method: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class PublicationConfig:
    publication_id: str
    outlet_name: str
    approved_publication: bool
    source_type: str
    enabled: bool = True
    critic_names: List[str] = field(default_factory=list)
    site_base_url: Optional[str] = None
    adapter: Optional[str] = None
    rt_source_path: Optional[str] = None
    rt_badge: Optional[str] = None
    sample_review_urls: List[str] = field(default_factory=list)
    review_url_count: Optional[int] = None
    dominant_host: Optional[str] = None
    inferred_review_path_prefix: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PublicationConfig":
        data = dict(payload)
        data["critic_names"] = normalize_critic_names(
            critic_names=data.get("critic_names"),
            critic_name=data.get("critic_name"),
        )
        data.pop("critic_name", None)
        return cls(**data)

    @property
    def critic_name(self) -> str:
        return resolve_primary_critic_name(critic_names=self.critic_names)


@dataclass
class ReviewRecord:
    publication_id: str
    outlet_name: str
    source_url: str
    canonical_url: Optional[str] = None
    headline: Optional[str] = None
    body_text: Optional[str] = None
    raw_score: Optional[str] = None
    published_at: Optional[str] = None
    critic_names: List[str] = field(default_factory=list)

    @property
    def critic_name(self) -> Optional[str]:
        return resolve_primary_critic_name(critic_names=self.critic_names) or None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "publication_id": self.publication_id,
            "outlet_name": self.outlet_name,
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "headline": self.headline,
            "body_text": self.body_text,
            "raw_score": self.raw_score,
            "published_at": self.published_at,
            "critic_name": self.critic_name,
            "critic_names": self.critic_names,
        }


class BaseScraper(ABC):
    source_name = "base"
    user_agent = "rtKalshiPred/0.1 (+https://example.local)"

    def __init__(self, publication: PublicationConfig, rule: SourceRule):
        self.publication = publication
        self.rule = rule
        self._fetch_cache: Dict[str, str] = {}
        self._fetch_cache_lock = RLock()

    def fetch_text(self, url: str) -> str:
        with self._fetch_cache_lock:
            cached = self._fetch_cache.get(url)
        if cached is not None:
            return cached
        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8", errors="replace")
        with self._fetch_cache_lock:
            if len(self._fetch_cache) >= 128:
                self._fetch_cache.pop(next(iter(self._fetch_cache)))
            self._fetch_cache[url] = payload
        return payload

    @abstractmethod
    def list_recent_urls(self) -> List[str]:
        """Discover recent review URLs for this publication."""

    @abstractmethod
    def scrape(self, url: str) -> Dict[str, object]:
        """Extract a review record from an article page."""

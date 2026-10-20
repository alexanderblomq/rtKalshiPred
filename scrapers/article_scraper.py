from __future__ import annotations

import html
import json
import re
import warnings
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from scrapers.base_scraper import BaseScraper, ReviewRecord
from utils.review_discovery_shared import prioritize_candidate_urls
from utils.review_url_filters import looks_like_article_url


DEFAULT_RECENT_URL_LIMIT = 24


class ArticleScraper(BaseScraper):
    source_name = "article"
    _SELECTOR_ATTR_PATTERN = re.compile(r"^(?P<selector>.+?)::attr\((?P<attr>[^)]+)\)$")

    def list_recent_urls(self):
        if not self.rule.discovery_url:
            return []

        html_text = self.fetch_text(self.rule.discovery_url)
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_text, flags=re.IGNORECASE)
        urls = []
        for href in hrefs:
            absolute = urljoin(self.rule.discovery_url, href)
            if self._is_allowed_review_url(absolute):
                urls.append(absolute)
        return prioritize_candidate_urls(
            urls,
            rule=self.rule,
            publication=self.publication,
            limit=DEFAULT_RECENT_URL_LIMIT,
        )

    def _is_allowed_review_url(self, url: str) -> bool:
        if not looks_like_article_url(url):
            return False
        if self.rule.allowed_url_prefixes and not any(url.startswith(prefix) for prefix in self.rule.allowed_url_prefixes):
            return False
        if self.rule.review_url_keywords and not any(keyword.lower() in url.lower() for keyword in self.rule.review_url_keywords):
            return False
        return True

    def scrape(self, url: str) -> Dict[str, object]:
        html_text = self.fetch_text(url)
        return self.parse_article_html(url, html_text)

    def parse_article_html(self, url: str, html_text: str) -> Dict[str, object]:
        soup = self._make_soup(html_text)
        json_ld_blocks = self._parse_json_ld_blocks(html_text)
        record = ReviewRecord(
            publication_id=self.publication.publication_id,
            outlet_name=self.publication.outlet_name,
            source_url=url,
            critic_names=[],
        )

        record.headline = self._extract_headline(html_text, soup, json_ld_blocks)
        record.published_at = self._extract_published_at(html_text, soup, json_ld_blocks)
        record.raw_score = self._extract_score(html_text, soup, json_ld_blocks)
        record.canonical_url = self._extract_canonical_url(url, html_text, soup)
        record.critic_names = self._extract_critic_names(html_text, soup, json_ld_blocks)
        record.body_text = self._extract_body(soup)

        return record.to_dict()

    def _extract_headline(self, html_text: str, soup: BeautifulSoup, json_ld_blocks: List[object]) -> Optional[str]:
        selector_value = self._extract_first_selector_value(soup, self.rule.headline_selectors)
        if selector_value:
            return selector_value

        json_ld = self._extract_json_ld_field(json_ld_blocks, "headline")
        if json_ld:
            return json_ld

        og_title = self._extract_meta_content(html_text, "property", "og:title")
        if og_title:
            return og_title

        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
        if title_match:
            return self._clean_text(title_match.group(1))
        return None

    def _extract_published_at(self, html_text: str, soup: BeautifulSoup, json_ld_blocks: List[object]) -> Optional[str]:
        selector_value = self._extract_first_selector_value(soup, self.rule.published_at_selectors)
        if selector_value:
            return selector_value

        for field in ("datePublished", "dateCreated", "uploadDate"):
            value = self._extract_json_ld_field(json_ld_blocks, field)
            if value:
                return value

        for meta_name in ("article:published_time", "pubdate", "date", "timestamp"):
            value = self._extract_meta_content(html_text, "property", meta_name)
            if value:
                return value
            value = self._extract_meta_content(html_text, "name", meta_name)
            if value:
                return value

        time_match = re.search(r"<time[^>]*datetime=[\"']([^\"']+)[\"']", html_text, flags=re.IGNORECASE)
        if time_match:
            return time_match.group(1).strip()
        return None

    def _extract_score(self, html_text: str, soup: BeautifulSoup, json_ld_blocks: List[object]) -> Optional[str]:
        selector_value = self._extract_first_selector_value(soup, self.rule.score_selectors)
        if selector_value:
            return selector_value

        meta_rating = self._extract_meta_content(html_text, "itemprop", "ratingValue")
        meta_best = self._extract_meta_content(html_text, "itemprop", "bestRating")
        if meta_rating and meta_best:
            return f"{meta_rating}/{meta_best}"

        rating_value = self._extract_json_ld_field(json_ld_blocks, "ratingValue", allow_numeric=True)
        best_rating = self._extract_json_ld_field(json_ld_blocks, "bestRating", allow_numeric=True)
        if rating_value is not None and best_rating is not None:
            return f"{rating_value}/{best_rating}"

        visible_text = soup.get_text(" ", strip=True)
        out_of_match = re.search(
            r"\b(?:rating|score|grade|411\s+rating)\b[:\s-]*([0-9]+(?:\.[0-9]+)?)\s*(?:out of|/)\s*([0-9]+(?:\.[0-9]+)?)",
            visible_text,
            flags=re.IGNORECASE,
        )
        if out_of_match:
            return f"{out_of_match.group(1).strip()}/{out_of_match.group(2).strip()}"

        rating_context_match = re.search(
            r"(rating|rated|score|stars?)[:\s]+([0-9](?:\.[0-9])?\s*/\s*[0-9](?:\.[0-9])?|[0-9]{1,3}\s*%)",
            visible_text,
            flags=re.IGNORECASE,
        )
        if rating_context_match:
            return rating_context_match.group(2).strip()

        grade_match = re.search(r"\b(grade|letter grade)[:\s]+([ABCDF][+-]?)\b", visible_text)
        if grade_match:
            return grade_match.group(2).strip()
        return None

    def _extract_critic_names(self, html_text: str, soup: BeautifulSoup, json_ld_blocks: List[object]) -> List[str]:
        selector_value = self._extract_first_selector_value(soup, self.rule.critic_name_selectors)
        if selector_value:
            return [selector_value]

        author_value = self._extract_json_ld_field(json_ld_blocks, "author")
        if author_value:
            if isinstance(author_value, str):
                return [author_value.strip()]

        json_ld_authors = self._extract_json_ld_authors(json_ld_blocks)
        if json_ld_authors:
            return json_ld_authors

        for attr_name, attr_value in (
            ("name", "author"),
            ("property", "author"),
            ("property", "article:author"),
            ("name", "parsely-author"),
        ):
            meta_value = self._extract_meta_content(html_text, attr_name, attr_value)
            if meta_value:
                return [meta_value]

        author_match = re.search(
            r'class=["\'][^"\']*author[^"\']*["\'][^>]*>\s*(?:<a[^>]*>)?\s*([^<]{3,80})\s*(?:</a>)?\s*<',
            html_text,
            flags=re.IGNORECASE,
        )
        if author_match:
            return [self._clean_text(author_match.group(1))]

        byline_match = re.search(r"\bBy\s+([A-Z][A-Za-z.\-'\s]{2,60})\b", soup.get_text(" ", strip=True))
        if byline_match:
            return [self._clean_text(byline_match.group(1))]
        return []

    def _extract_body(self, soup: BeautifulSoup) -> Optional[str]:
        selector_value = self._extract_joined_selector_value(soup, self.rule.body_selectors)
        if selector_value:
            return selector_value

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        container = (
            soup.find("article")
            or soup.find("main")
            or soup.body
        )
        if container is None:
            return None

        cleaned = [self._clean_text(str(p)) for p in container.find_all("p")]
        cleaned = [p for p in cleaned if p]
        if not cleaned:
            return None
        return "\n\n".join(cleaned[:12])

    def _extract_canonical_url(self, url: str, html_text: str, soup: BeautifulSoup) -> Optional[str]:
        selector_value = self._extract_first_selector_value(soup, self.rule.canonical_url_selectors)
        if selector_value:
            return urljoin(url, selector_value)

        canonical = self._extract_meta_content(html_text, "property", "og:url")
        if canonical:
            return urljoin(url, canonical)
        link = soup.select_one('link[rel~="canonical"][href]')
        if link:
            return urljoin(url, link["href"].strip())
        return url

    def _extract_meta_content(self, html_text: str, attr_name: str, attr_value: str) -> Optional[str]:
        pattern = rf"<meta[^>]+{attr_name}=[\"']{re.escape(attr_value)}[\"'][^>]+content=[\"']([^\"']+)[\"']"
        match = re.search(pattern, html_text, flags=re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))
        reverse_pattern = rf"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+{attr_name}=[\"']{re.escape(attr_value)}[\"']"
        match = re.search(reverse_pattern, html_text, flags=re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))
        return None

    def _parse_json_ld_blocks(self, html_text: str) -> List[object]:
        scripts = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        parsed_blocks: List[object] = []
        for index, script in enumerate(scripts, start=1):
            try:
                data = json.loads(html.unescape(script.strip()))
            except json.JSONDecodeError as exc:
                snippet = self._clean_text(script)[:120]
                global _malformed_jsonld_warning_count
                if _malformed_jsonld_warning_count < MAX_MALFORMED_JSONLD_WARNINGS:
                    warnings.warn(
                        f"Malformed JSON-LD block {index} skipped: {exc.msg} (line {exc.lineno}, column {exc.colno}). Snippet: {snippet}",
                        RuntimeWarning,
                    )
                    _malformed_jsonld_warning_count += 1
                continue
            parsed_blocks.append(data)
        return parsed_blocks

    def _extract_json_ld_field(self, json_ld_blocks: List[object], field_name: str, allow_numeric: bool = False) -> Optional[str]:
        for data in json_ld_blocks:
            value = self._walk_json_for_field(data, field_name)
            if isinstance(value, str):
                return value.strip()
            if allow_numeric and type(value) in (int, float):
                return str(value)
        return None

    def _extract_json_ld_authors(self, json_ld_blocks: List[object]) -> List[str]:
        authors: List[str] = []
        for data in json_ld_blocks:
            extracted = self._walk_json_for_field(data, "author")
            if isinstance(extracted, dict):
                name = extracted.get("name")
                if isinstance(name, str) and name.strip():
                    authors.append(name.strip())
            elif isinstance(extracted, list):
                for item in extracted:
                    if isinstance(item, dict):
                        name = item.get("name")
                        if isinstance(name, str) and name.strip():
                            authors.append(name.strip())
                    elif isinstance(item, str) and item.strip():
                        authors.append(item.strip())
            elif isinstance(extracted, str) and extracted.strip():
                authors.append(extracted.strip())
        deduped: List[str] = []
        for author in authors:
            if author not in deduped:
                deduped.append(author)
        return deduped

    def _extract_first_selector_value(self, soup: BeautifulSoup, selector_specs: List[str]) -> Optional[str]:
        for selector_spec in selector_specs:
            value = self._extract_selector_value(soup, selector_spec, join_all=False)
            if value:
                return value
        return None

    def _extract_joined_selector_value(self, soup: BeautifulSoup, selector_specs: List[str]) -> Optional[str]:
        for selector_spec in selector_specs:
            value = self._extract_selector_value(soup, selector_spec, join_all=True)
            if value:
                return value
        return None

    def _extract_selector_value(self, soup: BeautifulSoup, selector_spec: str, join_all: bool) -> Optional[str]:
        selector, attr_name = self._parse_selector_spec(selector_spec)
        try:
            nodes = soup.select(selector)
        except Exception as exc:
            warnings.warn(f"Invalid selector '{selector_spec}' skipped: {exc}", RuntimeWarning)
            return None

        if not nodes:
            return None

        if join_all:
            values = [self._extract_node_value(node, attr_name) for node in nodes]
            cleaned_values = [value for value in values if value]
            if cleaned_values:
                return "\n\n".join(cleaned_values)
            return None

        return self._extract_node_value(nodes[0], attr_name)

    def _parse_selector_spec(self, selector_spec: str) -> Tuple[str, Optional[str]]:
        match = self._SELECTOR_ATTR_PATTERN.match(selector_spec.strip())
        if match:
            return match.group("selector").strip(), match.group("attr").strip()
        return selector_spec.strip(), None

    def _extract_node_value(self, node, attr_name: Optional[str]) -> Optional[str]:
        if attr_name:
            value = node.get(attr_name)
            return self._clean_text(value) if value else None

        text_value = self._clean_text(node.get_text(" ", strip=True))
        if text_value:
            return text_value

        for fallback_attr in ("content", "href", "datetime", "src"):
            attr_value = node.get(fallback_attr)
            if attr_value:
                return self._clean_text(attr_value)
        return None

    def _walk_json_for_field(self, data, field_name: str):
        if isinstance(data, dict):
            if field_name in data:
                return data[field_name]
            for value in data.values():
                result = self._walk_json_for_field(value, field_name)
                if result is not None:
                    return result
        if isinstance(data, list):
            for item in data:
                result = self._walk_json_for_field(item, field_name)
                if result is not None:
                    return result
        return None

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        return " ".join(text.split()).strip()

    def _make_soup(self, html_text: str) -> BeautifulSoup:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            return BeautifulSoup(html_text, "html.parser")
MAX_MALFORMED_JSONLD_WARNINGS = 5
_malformed_jsonld_warning_count = 0

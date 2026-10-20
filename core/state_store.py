from __future__ import annotations

import json
import os
import re
import threading
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from utils.io import ensure_parent


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_title(title: str) -> str:
    text = title.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


@dataclass
class RuntimeState:
    title_id: str
    target_title: str
    accepted_reviews: List[Dict[str, Any]]
    rejected_events: List[Dict[str, Any]]
    seen_review_urls: Set[str]
    startup_backfill_complete: bool
    latest_snapshot: Dict[str, Any]
    rt_baseline: Dict[str, Any]


class RealtimeStateStore:
    def load_runtime_state(self, target_title: str) -> RuntimeState:
        raise NotImplementedError

    def append_accepted_review(self, target_title: str, review: Dict[str, Any]) -> None:
        raise NotImplementedError

    def append_rejected_event(self, target_title: str, event: Dict[str, Any]) -> None:
        raise NotImplementedError

    def append_engine_event(self, target_title: str, event: Dict[str, Any]) -> None:
        raise NotImplementedError

    def persist_snapshot(
        self,
        target_title: str,
        snapshot: Dict[str, Any],
        startup_backfill_complete: bool,
        seen_review_urls: Set[str],
        rt_baseline: Dict[str, Any],
    ) -> None:
        raise NotImplementedError

    def delete_title_state(self, target_title: str) -> None:
        raise NotImplementedError


class FileSystemRealtimeStateStore(RealtimeStateStore):
    def __init__(self, root_dir: str = "data/live") -> None:
        self.root_dir = Path(root_dir)
        self._write_lock = threading.RLock()

    def load_runtime_state(self, target_title: str) -> RuntimeState:
        title_id = slugify_title(target_title)
        title_dir = self._title_dir(title_id)
        state = self._read_json(title_dir / "state.json", default={})
        snapshots = self._read_jsonl(title_dir / "snapshots.jsonl")
        engine_events = self._read_jsonl(title_dir / "events.jsonl")
        accepted_reviews = self._read_jsonl(title_dir / "accepted_reviews.jsonl")
        rejected_events = self._read_jsonl(title_dir / "rejected_events.jsonl")

        accepted_reviews = self._reconcile_accepted_reviews(accepted_reviews, engine_events)
        rejected_events = self._reconcile_rejected_events(rejected_events, engine_events)
        latest_snapshot = self._resolve_latest_snapshot(state, snapshots)
        rt_baseline = self._resolve_rt_baseline(state, latest_snapshot, engine_events)

        seen_urls = set(str(url) for url in state.get("seen_review_urls", []) if url)
        seen_urls.update(self._extract_seen_urls_from_reviews(accepted_reviews))
        seen_urls.update(self._extract_permanent_rejected_urls(rejected_events))
        seen_urls.update(self._extract_seen_urls_from_events(engine_events))

        return RuntimeState(
            title_id=title_id,
            target_title=target_title,
            accepted_reviews=accepted_reviews,
            rejected_events=rejected_events,
            seen_review_urls=seen_urls,
            startup_backfill_complete=self._resolve_startup_backfill_complete(state, latest_snapshot, engine_events),
            latest_snapshot=latest_snapshot,
            rt_baseline=rt_baseline,
        )

    def append_accepted_review(self, target_title: str, review: Dict[str, Any]) -> None:
        self._append_jsonl(self._title_dir_for_title(target_title) / "accepted_reviews.jsonl", review)

    def append_rejected_event(self, target_title: str, event: Dict[str, Any]) -> None:
        self._append_jsonl(self._title_dir_for_title(target_title) / "rejected_events.jsonl", event)

    def append_engine_event(self, target_title: str, event: Dict[str, Any]) -> None:
        payload = {"recorded_at": _utc_now_iso(), **event}
        self._append_jsonl(self._title_dir_for_title(target_title) / "events.jsonl", payload)

    def persist_snapshot(
        self,
        target_title: str,
        snapshot: Dict[str, Any],
        startup_backfill_complete: bool,
        seen_review_urls: Set[str],
        rt_baseline: Dict[str, Any],
    ) -> None:
        title_dir = self._title_dir_for_title(target_title)
        snapshot_with_timestamp = {"recorded_at": _utc_now_iso(), **snapshot}
        self._append_jsonl(title_dir / "snapshots.jsonl", snapshot_with_timestamp)
        state = {
            "title_id": slugify_title(target_title),
            "target_title": target_title,
            "updated_at": _utc_now_iso(),
            "startup_backfill_complete": startup_backfill_complete,
            "seen_review_urls": sorted(seen_review_urls),
            "latest_snapshot": snapshot,
            "rt_baseline": rt_baseline,
        }
        self._write_json(title_dir / "state.json", state)

    def delete_title_state(self, target_title: str) -> None:
        title_dir = self._title_dir_for_title(target_title)
        if not title_dir.exists():
            return
        for child in title_dir.iterdir():
            if child.is_file():
                child.unlink()
        title_dir.rmdir()

    def _title_dir_for_title(self, target_title: str) -> Path:
        return self._title_dir(slugify_title(target_title))

    def _title_dir(self, title_id: str) -> Path:
        return self.root_dir / title_id

    def _append_jsonl(self, path: Path, payload: Dict[str, Any]) -> None:
        ensure_parent(str(path))
        line = json.dumps(payload, ensure_ascii=True) + "\n"
        with self._write_lock:
            self._recover_jsonl_tail(path)
            if path.exists() and path.stat().st_size:
                with path.open("rb") as existing:
                    existing.seek(-1, os.SEEK_END)
                    if existing.read(1) != b"\n":
                        line = "\n" + line
            with path.open("a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        ensure_parent(str(path))
        tmp_path = path.with_name(f"{path.name}.tmp")
        encoded = json.dumps(payload, indent=2, ensure_ascii=True)
        with self._write_lock:
            with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write(encoded)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)

    def _read_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        if not path.exists():
            return dict(default)
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        self._recover_jsonl_tail(path)
        rows: List[Dict[str, Any]] = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    def _recover_jsonl_tail(self, path: Path) -> None:
        """Preserve an interrupted final append; corruption elsewhere stays fatal."""
        with self._write_lock:
            if not path.exists() or not path.stat().st_size:
                return
            with path.open("rb") as handle:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) == b"\n":
                    return
            content = path.read_bytes()
            offset = content.rfind(b"\n") + 1
            tail = content[offset:]
            try:
                json.loads(tail)
            except (json.JSONDecodeError, UnicodeDecodeError):
                recovery_path = path.with_name(path.name + ".incomplete")
                with recovery_path.open("ab") as recovery:
                    recovery.write(tail + b"\n")
                    recovery.flush()
                    os.fsync(recovery.fileno())
                with path.open("r+b") as handle:
                    handle.truncate(offset)
                    handle.flush()
                    os.fsync(handle.fileno())
                warnings.warn(f"Recovered incomplete final record in {path}; saved to {recovery_path}", RuntimeWarning)

    def _reconcile_accepted_reviews(
        self,
        accepted_reviews: List[Dict[str, Any]],
        engine_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        reconciled: List[Dict[str, Any]] = []
        seen_urls: Set[str] = set()
        for review in accepted_reviews:
            canonical_url = self._accepted_review_url(review)
            if not canonical_url or canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)
            reconciled.append(review)

        for event in engine_events:
            if event.get("event_type") != "review_accepted":
                continue
            accepted_record = event.get("accepted_record")
            if not isinstance(accepted_record, dict):
                continue
            canonical_url = self._accepted_review_url(accepted_record)
            if not canonical_url or canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)
            reconciled.append(dict(accepted_record))
        return reconciled

    def _reconcile_rejected_events(
        self,
        rejected_events: List[Dict[str, Any]],
        engine_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        reconciled: List[Dict[str, Any]] = list(rejected_events)
        seen_keys = {
            (str(item.get("url") or ""), str(item.get("reason") or ""), bool(self._is_retryable_rejection(item)))
            for item in rejected_events
        }
        for event in engine_events:
            if event.get("event_type") != "review_rejected":
                continue
            rejected_record = event.get("rejected_record")
            if not isinstance(rejected_record, dict):
                continue
            key = (
                str(rejected_record.get("url") or ""),
                str(rejected_record.get("reason") or ""),
                bool(self._is_retryable_rejection(rejected_record)),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            reconciled.append(dict(rejected_record))
        return reconciled

    def _resolve_latest_snapshot(
        self,
        state: Dict[str, Any],
        snapshots: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if snapshots:
            latest = dict(snapshots[-1])
            latest.pop("recorded_at", None)
            return latest
        latest_snapshot = state.get("latest_snapshot", {})
        return dict(latest_snapshot) if isinstance(latest_snapshot, dict) else {}

    def _resolve_rt_baseline(
        self,
        state: Dict[str, Any],
        latest_snapshot: Dict[str, Any],
        engine_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        rt_baseline = state.get("rt_baseline")
        if isinstance(rt_baseline, dict) and rt_baseline:
            return dict(rt_baseline)

        if latest_snapshot:
            diagnostics = latest_snapshot.get("official_rt_diagnostics") or {}
            if any(
                latest_snapshot.get(key) is not None
                for key in ("official_rt_review_count", "official_rt_tomatometer", "official_rt_title_path")
            ) or diagnostics:
                return {
                    "review_count": latest_snapshot.get("official_rt_review_count"),
                    "tomatometer": latest_snapshot.get("official_rt_tomatometer"),
                    "rt_title_path": latest_snapshot.get("official_rt_title_path"),
                    "diagnostics": diagnostics,
                }

        for event in reversed(engine_events):
            if event.get("event_type") not in {"rt_baseline_synced", "rt_baseline_sync_incomplete", "rt_baseline_sync_failed"}:
                continue
            return {
                "review_count": event.get("review_count"),
                "tomatometer": event.get("tomatometer"),
                "rt_title_path": event.get("rt_title_path"),
                "diagnostics": dict(event.get("diagnostics", {})),
                "available": event.get("event_type") == "rt_baseline_synced",
            }
        return {}

    def _resolve_startup_backfill_complete(
        self,
        state: Dict[str, Any],
        latest_snapshot: Dict[str, Any],
        engine_events: List[Dict[str, Any]],
    ) -> bool:
        if state.get("startup_backfill_complete"):
            return True
        if latest_snapshot.get("startup_backfill_complete"):
            return True
        return any(event.get("event_type") == "startup_backfill_completed" for event in engine_events)

    def _extract_seen_urls_from_reviews(self, accepted_reviews: Iterable[Dict[str, Any]]) -> Set[str]:
        seen_urls: Set[str] = set()
        for review in accepted_reviews:
            for value in self._iter_review_urls(review):
                seen_urls.add(value)
        return seen_urls

    def _extract_permanent_rejected_urls(self, rejected_events: Iterable[Dict[str, Any]]) -> Set[str]:
        seen_urls: Set[str] = set()
        for event in rejected_events:
            if self._is_retryable_rejection(event):
                continue
            for value in self._iter_review_urls(event):
                seen_urls.add(value)
        return seen_urls

    def _extract_seen_urls_from_events(self, engine_events: Iterable[Dict[str, Any]]) -> Set[str]:
        seen_urls: Set[str] = set()
        for event in engine_events:
            event_type = event.get("event_type")
            if event_type == "review_accepted":
                accepted_record = event.get("accepted_record")
                if isinstance(accepted_record, dict):
                    seen_urls.update(self._iter_review_urls(accepted_record))
                for value in self._iter_review_urls(event):
                    seen_urls.add(value)
            elif event_type == "review_rejected":
                rejected_record = event.get("rejected_record")
                if isinstance(rejected_record, dict) and not self._is_retryable_rejection(rejected_record):
                    seen_urls.update(self._iter_review_urls(rejected_record))
                elif not self._is_retryable_rejection(event):
                    for value in self._iter_review_urls(event):
                        seen_urls.add(value)
        return seen_urls

    def _accepted_review_url(self, review: Dict[str, Any]) -> Optional[str]:
        for value in self._iter_review_urls(review):
            return value
        return None

    def _iter_review_urls(self, payload: Dict[str, Any]) -> Iterable[str]:
        for key in ("url", "canonical_url", "source_url"):
            value = payload.get(key)
            if value:
                yield str(value)
        aliases = payload.get("seen_url_aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if alias:
                    yield str(alias)

    def _is_retryable_rejection(self, payload: Dict[str, Any]) -> bool:
        if "retryable" in payload:
            return bool(payload.get("retryable"))
        return str(payload.get("reason") or "") in {"scrape_failed", "transient_error", "timeout"}


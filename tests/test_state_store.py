import json

from core.state_store import FileSystemRealtimeStateStore


def test_file_system_state_store_round_trips_runtime_state(state_store_root):
    root_dir = state_store_root
    store = FileSystemRealtimeStateStore(root_dir=str(root_dir))
    title = "Animal Farm"

    store.append_accepted_review(title, {"url": "https://example.com/review-1", "fresh_probability": 0.8})
    store.append_rejected_event(title, {"url": "https://example.com/review-2", "reason": "low_title_confidence"})
    store.append_engine_event(title, {"event_type": "review_accepted", "url": "https://example.com/review-1"})
    store.persist_snapshot(
        title,
        snapshot={"review_count": 1, "calculated_tomatometer": 80.0},
        startup_backfill_complete=True,
        seen_review_urls={"https://example.com/review-1", "https://example.com/review-2"},
        rt_baseline={"review_count": 5, "tomatometer": 73.0, "rt_title_path": "m/animal_farm_2025"},
    )

    runtime_state = store.load_runtime_state(title)

    assert runtime_state.title_id == "animal-farm"
    assert runtime_state.startup_backfill_complete is True
    assert len(runtime_state.accepted_reviews) == 1
    assert len(runtime_state.rejected_events) == 1
    assert runtime_state.latest_snapshot["review_count"] == 1
    assert runtime_state.rt_baseline["review_count"] == 5
    assert "https://example.com/review-1" in runtime_state.seen_review_urls
    assert "https://example.com/review-2" in runtime_state.seen_review_urls

    state_path = root_dir / "animal-farm" / "state.json"
    snapshots_path = root_dir / "animal-farm" / "snapshots.jsonl"
    events_path = root_dir / "animal-farm" / "events.jsonl"

    assert state_path.exists()
    assert snapshots_path.exists()
    assert events_path.exists()
    assert json.loads(state_path.read_text(encoding="utf-8"))["latest_snapshot"]["calculated_tomatometer"] == 80.0


def test_file_system_state_store_can_delete_title_state(state_store_root):
    root_dir = state_store_root
    store = FileSystemRealtimeStateStore(root_dir=str(root_dir))
    title = "Animal Farm"

    store.append_accepted_review(title, {"url": "https://example.com/review-1"})

    title_dir = root_dir / "animal-farm"
    assert title_dir.exists()

    store.delete_title_state(title)

    assert not title_dir.exists()

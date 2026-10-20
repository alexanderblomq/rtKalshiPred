from __future__ import annotations

import json

from pipelines.validate_rt_signal import (
    _load_title_specs,
    summarize_validation_results,
    validate_title_signal,
)
from core.state_store import FileSystemRealtimeStateStore


def test_load_title_specs_reads_manifest(registry_root):
    manifest = registry_root / "titles.json"
    manifest.write_text(
        json.dumps(
            [
                {"title": "Animal Farm", "rt_title_path": "m/animal_farm_2025"},
                {"title": "Blue Heron"},
            ]
        ),
        encoding="utf-8",
    )

    specs = _load_title_specs(str(manifest), [])

    assert specs[0]["title"] == "Animal Farm"
    assert specs[0]["rt_title_path"] == "m/animal_farm_2025"
    assert specs[1]["title"] == "Blue Heron"


def test_validate_title_signal_reports_score_error_and_contract_metrics(registry_root):
    state_root = registry_root / "live_validation"
    store = FileSystemRealtimeStateStore(root_dir=str(state_root))
    title = "Animal Farm"

    store.append_accepted_review(
        title,
        {
            "url": "https://critic.example/review-1",
            "publication_id": "variety",
            "critic_name": "Critic One",
            "fresh_probability": 0.9,
            "recorded_at": "2026-04-20T12:00:00+00:00",
        },
    )
    store.append_accepted_review(
        title,
        {
            "url": "https://critic.example/review-2",
            "publication_id": "newyorker",
            "critic_name": "Critic Two",
            "fresh_probability": 0.7,
            "recorded_at": "2026-04-21T12:00:00+00:00",
        },
    )
    store.persist_snapshot(
        title,
        snapshot={
            "calculated_tomatometer": 82.0,
            "official_rt_tomatometer": 80.0,
            "official_rt_review_count": 5,
            "official_rt_title_path": "m/animal_farm_2025",
            "official_rt_diagnostics": {"fetch_status": "ok"},
            "system_review_count": 2,
        },
        startup_backfill_complete=True,
        seen_review_urls={
            "https://critic.example/review-1",
            "https://critic.example/review-2",
        },
        rt_baseline={
            "review_count": 5,
            "tomatometer": 80.0,
            "rt_title_path": "m/animal_farm_2025",
            "diagnostics": {"fetch_status": "ok"},
        },
    )

    result = validate_title_signal(
        title_spec={
            "title": title,
            "contracts": [
                {
                    "ticker": "RT_ABOVE_80",
                    "title": "Will Animal Farm score above 80% on Rotten Tomatoes?",
                    "floor_strike": 0.80,
                    "market_yes_probability": 0.45,
                },
                {
                    "ticker": "RT_BETWEEN_75_84",
                    "title": "Will Animal Farm score between 75% and 84% on Rotten Tomatoes?",
                    "floor_strike": 0.75,
                    "cap_strike": 0.84,
                    "market_yes_probability": 0.50,
                },
            ],
        },
        publication_ids=["variety", "newyorker"],
        state_backend="filesystem",
        state_root=str(state_root),
        sqlite_path=None,
        backfill_max_publications=10,
        poll_workers=1,
        process_workers=1,
        skip_rt_sync=True,
        refresh=False,
    )

    assert result["calculated_tomatometer"] == 82.0
    assert result["official_rt_tomatometer"] == 80.0
    assert result["score_error"] == 2.0
    assert result["coverage"]["coverage_ratio"] == 0.4
    assert result["timeline"]["publication_coverage_count"] == 2
    assert result["contract_summary"]["contract_count"] == 2
    assert result["contract_summary"]["trade_count"] >= 1
    assert result["contract_results"][0]["ticker"] == "RT_ABOVE_80"


def test_summarize_validation_results_aggregates_metrics():
    summary = summarize_validation_results(
        [
            {
                "official_rt_tomatometer": 80.0,
                "absolute_score_error": 2.0,
                "coverage": {"coverage_ratio": 0.4},
                "contract_summary": {
                    "average_brier_score": 0.09,
                    "simulated_total_pnl": 0.12,
                    "trade_count": 2,
                },
            },
            {
                "official_rt_tomatometer": 70.0,
                "absolute_score_error": 4.0,
                "coverage": {"coverage_ratio": 0.5},
                "contract_summary": {
                    "average_brier_score": 0.16,
                    "simulated_total_pnl": -0.03,
                    "trade_count": 1,
                },
            },
        ]
    )

    assert summary["title_count"] == 2
    assert summary["titles_with_official_rt"] == 2
    assert summary["mean_absolute_score_error"] == 3.0
    assert summary["mean_coverage_ratio"] == 0.45
    assert summary["mean_contract_brier_score"] == 0.125
    assert summary["simulated_total_pnl"] == 0.09
    assert summary["simulated_trade_count"] == 3

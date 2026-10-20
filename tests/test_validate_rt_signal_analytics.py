from __future__ import annotations

from pipelines.validate_rt_signal import (
    _contract_rule_family,
    _publication_contribution_metrics,
    _review_timeline_metrics,
    _summarize_contract_results_by_rule_family,
    build_validation_summary_markdown,
    summarize_validation_results,
)


def test_review_timeline_metrics_computes_span_and_interarrival_hours():
    metrics = _review_timeline_metrics(
        [
            {"recorded_at": "2026-04-20T12:00:00+00:00", "publication_id": "variety", "critic_name": "A"},
            {"recorded_at": "2026-04-20T18:00:00+00:00", "publication_id": "variety", "critic_name": "B"},
            {"recorded_at": "2026-04-21T12:00:00+00:00", "publication_id": "newyorker", "critic_names": ["C", "D"]},
        ]
    )

    assert metrics["first_review_seen_at"] == "2026-04-20T12:00:00+00:00"
    assert metrics["last_review_seen_at"] == "2026-04-21T12:00:00+00:00"
    assert metrics["observed_review_span_hours"] == 24.0
    assert metrics["observed_review_interarrival_hours"] == [6.0, 18.0]
    assert metrics["median_interarrival_hours"] == 12.0
    assert metrics["publication_coverage_count"] == 2
    assert metrics["critic_coverage_count"] == 4


def test_publication_contribution_metrics_aggregates_review_share_and_critics():
    contributions = _publication_contribution_metrics(
        [
            {
                "publication_id": "variety",
                "outlet_name": "Variety",
                "critic_name": "Critic One",
                "fresh_probability": 0.9,
                "recorded_at": "2026-04-20T12:00:00+00:00",
            },
            {
                "publication_id": "variety",
                "outlet_name": "Variety",
                "critic_names": ["Critic Two"],
                "fresh_probability": 0.5,
                "recorded_at": "2026-04-20T13:00:00+00:00",
            },
            {
                "publication_id": "newyorker",
                "outlet_name": "The New Yorker",
                "critic_name": "Critic Three",
                "fresh_probability": 0.2,
                "recorded_at": "2026-04-21T12:00:00+00:00",
            },
        ]
    )

    assert contributions[0]["publication_id"] == "variety"
    assert contributions[0]["review_count"] == 2
    assert contributions[0]["share_of_observed_reviews"] == 0.6667
    assert contributions[0]["average_fresh_probability"] == 0.7
    assert contributions[0]["critic_count"] == 2
    assert contributions[0]["share_of_expected_freshness"] == 0.875
    assert contributions[1]["publication_id"] == "newyorker"
    assert contributions[1]["share_of_expected_freshness"] == 0.125


def test_contract_rule_family_and_rule_family_summary_cover_thresholds_and_ranges():
    assert _contract_rule_family({"floor_strike": 0.8}) == "threshold_above"
    assert _contract_rule_family({"cap_strike": 0.7}) == "threshold_below"
    assert _contract_rule_family({"floor_strike": 0.75, "cap_strike": 0.84}) == "between_range"

    summary = _summarize_contract_results_by_rule_family(
        [
            {
                "rule_family": "threshold_above",
                "edge": 0.11,
                "trade_recommendation": "BUY YES",
                "brier_score": 0.09,
                "simulated_trade_pnl": 0.2,
            },
            {
                "rule_family": "threshold_above",
                "edge": -0.03,
                "trade_recommendation": "NO TRADE",
                "brier_score": 0.16,
                "simulated_trade_pnl": 0.0,
            },
            {
                "rule_family": "between_range",
                "edge": -0.08,
                "trade_recommendation": "BUY NO",
                "brier_score": 0.04,
                "simulated_trade_pnl": 0.12,
            },
        ]
    )

    above = next(item for item in summary if item["rule_family"] == "threshold_above")
    between = next(item for item in summary if item["rule_family"] == "between_range")
    assert above["contract_count"] == 2
    assert above["trade_count"] == 1
    assert above["average_edge"] == 0.04
    assert above["average_brier_score"] == 0.125
    assert above["win_rate"] == 1.0
    assert between["simulated_total_pnl"] == 0.12


def test_summarize_validation_results_includes_rule_family_and_publication_analytics():
    summary = summarize_validation_results(
        [
            {
                "official_rt_tomatometer": 80.0,
                "absolute_score_error": 2.0,
                "coverage": {"coverage_ratio": 0.4},
                "timeline": {"observed_review_span_hours": 24.0, "median_interarrival_hours": 12.0},
                "publication_contributions": [
                    {
                        "publication_id": "variety",
                        "outlet_name": "Variety",
                        "review_count": 2,
                        "share_of_observed_reviews": 0.5,
                        "share_of_expected_freshness": 0.6,
                        "fresh_probability_sum": 1.3,
                        "critic_names": ["A", "B"],
                    }
                ],
                "contract_summary": {
                    "average_brier_score": 0.09,
                    "simulated_total_pnl": 0.12,
                    "trade_count": 2,
                },
                "contract_results": [
                    {
                        "rule_family": "threshold_above",
                        "edge": 0.1,
                        "brier_score": 0.09,
                        "trade_recommendation": "BUY YES",
                        "simulated_trade_pnl": 0.12,
                    }
                ],
            },
            {
                "official_rt_tomatometer": 70.0,
                "absolute_score_error": 4.0,
                "coverage": {"coverage_ratio": 0.5},
                "timeline": {"observed_review_span_hours": 10.0, "median_interarrival_hours": 5.0},
                "publication_contributions": [
                    {
                        "publication_id": "variety",
                        "outlet_name": "Variety",
                        "review_count": 1,
                        "share_of_observed_reviews": 0.25,
                        "share_of_expected_freshness": 0.4,
                        "fresh_probability_sum": 0.4,
                        "critic_names": ["C"],
                    },
                    {
                        "publication_id": "newyorker",
                        "outlet_name": "The New Yorker",
                        "review_count": 3,
                        "share_of_observed_reviews": 0.75,
                        "share_of_expected_freshness": 0.6,
                        "fresh_probability_sum": 1.8,
                        "critic_names": ["D", "E"],
                    },
                ],
                "contract_summary": {
                    "average_brier_score": 0.16,
                    "simulated_total_pnl": -0.03,
                    "trade_count": 1,
                },
                "contract_results": [
                    {
                        "rule_family": "between_range",
                        "edge": -0.08,
                        "brier_score": 0.16,
                        "trade_recommendation": "BUY NO",
                        "simulated_trade_pnl": -0.03,
                    }
                ],
            },
        ]
    )

    assert summary["mean_observed_review_span_hours"] == 17.0
    assert summary["mean_median_interarrival_hours"] == 8.5
    assert summary["rule_family_summary"][0]["rule_family"] == "between_range"
    assert summary["rule_family_summary"][1]["rule_family"] == "threshold_above"
    assert summary["publication_contribution_summary"][0]["publication_id"] == "newyorker"
    assert summary["publication_contribution_summary"][1]["publication_id"] == "variety"


def test_build_validation_summary_markdown_includes_sections():
    markdown = build_validation_summary_markdown(
        {
            "summary": {
                "title_count": 2,
                "titles_with_official_rt": 2,
                "mean_absolute_score_error": 3.0,
                "mean_coverage_ratio": 0.45,
                "mean_contract_brier_score": 0.125,
                "simulated_total_pnl": 0.09,
                "simulated_trade_count": 3,
                "rule_family_summary": [
                    {
                        "rule_family": "threshold_above",
                        "contract_count": 2,
                        "trade_count": 1,
                        "average_edge": 0.04,
                        "average_brier_score": 0.125,
                        "simulated_total_pnl": 0.12,
                        "win_rate": 1.0,
                    }
                ],
                "publication_contribution_summary": [
                    {
                        "publication_id": "variety",
                        "title_count": 2,
                        "review_count": 3,
                        "average_reviews_per_title": 1.5,
                        "average_share_of_observed_reviews": 0.375,
                    }
                ],
            },
            "results": [
                {
                    "title": "Animal Farm",
                    "calculated_tomatometer": 82.0,
                    "official_rt_tomatometer": 80.0,
                    "absolute_score_error": 2.0,
                    "coverage": {"coverage_ratio": 0.4},
                    "system_review_count": 2,
                }
            ],
        }
    )

    assert "# RT Signal Validation Summary" in markdown
    assert "## Rule Family Performance" in markdown
    assert "`threshold_above`" in markdown
    assert "**Animal Farm**" in markdown

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from statistics import median
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from main import PUBLICATION_PRESETS
from realtime_tomatometer import RealtimeTomatometerEngine
from state_store import FileSystemRealtimeStateStore, RealtimeStateStore, SQLiteRealtimeStateStore
from trading_signal import score_probability_for_contract
from utils.logging import configure_file_logger


DEFAULT_THRESHOLD_CONTRACTS: List[Dict[str, Any]] = [
    {
        "ticker": "RT_ABOVE_60",
        "title": "Will the movie score above 60% on Rotten Tomatoes?",
        "floor_strike": 0.60,
        "market_yes_probability": 0.50,
    },
    {
        "ticker": "RT_ABOVE_70",
        "title": "Will the movie score above 70% on Rotten Tomatoes?",
        "floor_strike": 0.70,
        "market_yes_probability": 0.50,
    },
    {
        "ticker": "RT_ABOVE_80",
        "title": "Will the movie score above 80% on Rotten Tomatoes?",
        "floor_strike": 0.80,
        "market_yes_probability": 0.50,
    },
    {
        "ticker": "RT_BETWEEN_75_84",
        "title": "Will the movie score between 75% and 84% on Rotten Tomatoes?",
        "floor_strike": 0.75,
        "cap_strike": 0.84,
        "market_yes_probability": 0.50,
    },
]


def _build_state_store(state_backend: str, state_root: str, sqlite_path: str | None) -> RealtimeStateStore:
    if state_backend == "sqlite":
        path = sqlite_path or str(Path(state_root) / "validation.sqlite3")
        return SQLiteRealtimeStateStore(db_path=path)
    return FileSystemRealtimeStateStore(root_dir=state_root)


def _resolve_publication_ids(publication_ids: List[str] | None, publication_preset: str | None) -> List[str] | None:
    items: List[str] = []
    if publication_preset:
        items.extend(PUBLICATION_PRESETS[publication_preset])
    if publication_ids:
        items.extend(publication_ids)
    deduped = list(dict.fromkeys(items))
    return deduped or None


def _load_title_specs(manifest_path: Optional[str], titles: Iterable[str]) -> List[Dict[str, Any]]:
    specs = [{"title": title} for title in titles]
    if not manifest_path:
        return specs
    payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Validation manifest must be a JSON list of title specs.")
    return [dict(item) for item in payload]


def _coerce_score_percent(value: Any) -> Optional[float]:
    if value is None:
        return None
    score = float(value)
    if 0.0 <= score <= 1.0:
        score *= 100.0
    return score


def _estimate_score_stdev(snapshot: Dict[str, Any], review_count: int) -> float:
    explicit = snapshot.get("score_stdev")
    if explicit is not None:
        return max(1.0, float(explicit))
    if review_count <= 0:
        return 12.0
    if review_count <= 3:
        return 10.0
    if review_count <= 8:
        return 8.0
    if review_count <= 15:
        return 6.0
    return 5.0


def _observed_review_count(accepted_reviews: List[Dict[str, Any]]) -> int:
    return sum(1 for review in accepted_reviews if review.get("fresh_probability") is not None)


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _format_timestamp(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _review_timeline_metrics(accepted_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    seen_times: List[datetime] = []
    publications = set()
    critics = set()
    for review in accepted_reviews:
        recorded_at = review.get("recorded_at") or review.get("accepted_at") or review.get("published_at")
        parsed_time = _parse_timestamp(recorded_at)
        if parsed_time:
            seen_times.append(parsed_time)
        publication_id = review.get("publication_id")
        if publication_id:
            publications.add(str(publication_id))
        critic_name = review.get("critic_name")
        if critic_name:
            critics.add(str(critic_name))
        critic_names = review.get("critic_names")
        if isinstance(critic_names, list):
            critics.update(str(name) for name in critic_names if name)

    sorted_times = sorted(seen_times)
    inter_review_hours = [
        round((current - previous).total_seconds() / 3600.0, 4)
        for previous, current in zip(sorted_times, sorted_times[1:])
    ]
    span_hours = None
    if len(sorted_times) >= 2:
        span_hours = round((sorted_times[-1] - sorted_times[0]).total_seconds() / 3600.0, 4)

    return {
        "first_review_seen_at": _format_timestamp(sorted_times[0]) if sorted_times else None,
        "last_review_seen_at": _format_timestamp(sorted_times[-1]) if sorted_times else None,
        "observed_review_span_hours": span_hours,
        "observed_review_interarrival_hours": inter_review_hours,
        "median_interarrival_hours": round(float(median(inter_review_hours)), 4) if inter_review_hours else None,
        "publication_coverage_count": len(publications),
        "critic_coverage_count": len(critics),
    }


def _coverage_metrics(snapshot: Dict[str, Any], accepted_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    official_rt_review_count = snapshot.get("official_rt_review_count")
    observed_count = _observed_review_count(accepted_reviews)
    coverage_ratio = None
    if official_rt_review_count:
        coverage_ratio = observed_count / max(int(official_rt_review_count), 1)
    return {
        "observed_review_count": observed_count,
        "official_rt_review_count": official_rt_review_count,
        "coverage_ratio": round(float(coverage_ratio), 4) if coverage_ratio is not None else None,
    }


def _publication_contribution_metrics(accepted_reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    total_reviews = max(len(accepted_reviews), 1)
    total_expected_fresh = sum(
        float(review.get("fresh_probability", 0.0) or 0.0)
        for review in accepted_reviews
        if review.get("fresh_probability") is not None
    )
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "publication_id": "",
            "outlet_name": None,
            "review_count": 0,
            "fresh_probability_sum": 0.0,
            "fresh_probability_values": [],
            "critic_names": set(),
            "first_seen_at": None,
            "last_seen_at": None,
        }
    )

    for review in accepted_reviews:
        publication_id = str(review.get("publication_id") or "unknown")
        bucket = buckets[publication_id]
        bucket["publication_id"] = publication_id
        bucket["outlet_name"] = review.get("outlet_name") or bucket["outlet_name"]
        bucket["review_count"] += 1
        fresh_probability = review.get("fresh_probability")
        if fresh_probability is not None:
            fp = float(fresh_probability)
            bucket["fresh_probability_sum"] += fp
            bucket["fresh_probability_values"].append(fp)
        critic_name = review.get("critic_name")
        if critic_name:
            bucket["critic_names"].add(str(critic_name))
        critic_names = review.get("critic_names")
        if isinstance(critic_names, list):
            bucket["critic_names"].update(str(name) for name in critic_names if name)
        seen_at = _parse_timestamp(review.get("recorded_at") or review.get("accepted_at") or review.get("published_at"))
        if seen_at is not None:
            if bucket["first_seen_at"] is None or seen_at < bucket["first_seen_at"]:
                bucket["first_seen_at"] = seen_at
            if bucket["last_seen_at"] is None or seen_at > bucket["last_seen_at"]:
                bucket["last_seen_at"] = seen_at

    results: List[Dict[str, Any]] = []
    for publication_id, bucket in buckets.items():
        freshness_values = bucket["fresh_probability_values"]
        avg_fresh_probability = None
        if freshness_values:
            avg_fresh_probability = sum(freshness_values) / len(freshness_values)
        fresh_probability_sum = float(bucket["fresh_probability_sum"])
        results.append(
            {
                "publication_id": publication_id,
                "outlet_name": bucket["outlet_name"],
                "review_count": int(bucket["review_count"]),
                "share_of_observed_reviews": round(int(bucket["review_count"]) / total_reviews, 4),
                "fresh_probability_sum": round(fresh_probability_sum, 4),
                "share_of_expected_freshness": round(fresh_probability_sum / total_expected_fresh, 4)
                if total_expected_fresh > 0.0
                else None,
                "average_fresh_probability": round(float(avg_fresh_probability), 4) if avg_fresh_probability is not None else None,
                "critic_count": len(bucket["critic_names"]),
                "critic_names": sorted(bucket["critic_names"]),
                "first_seen_at": _format_timestamp(bucket["first_seen_at"]),
                "last_seen_at": _format_timestamp(bucket["last_seen_at"]),
            }
        )
    results.sort(key=lambda item: (-int(item["review_count"]), item["publication_id"]))
    return results


def _contract_rule_family(contract: Dict[str, Any]) -> str:
    floor_strike = contract.get("floor_strike")
    cap_strike = contract.get("cap_strike")
    title = str(contract.get("title") or contract.get("subtitle") or "").lower()
    if floor_strike is not None and cap_strike is not None:
        return "between_range"
    if floor_strike is not None:
        return "threshold_above"
    if cap_strike is not None:
        return "threshold_below"
    if "fresh" in title or "rotten" in title:
        return "binary_freshness"
    return "other"


def _evaluate_contracts(
    predicted_score: Optional[float],
    official_score: Optional[float],
    score_stdev: float,
    contracts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if predicted_score is None:
        return results
    for contract in contracts:
        model_prob = score_probability_for_contract(predicted_score, score_stdev, contract)
        market_prob = float(contract.get("market_yes_probability", 0.50))
        rule_family = _contract_rule_family(contract)
        resolved_yes = None
        brier_score = None
        if official_score is not None:
            resolved_yes = score_probability_for_contract(official_score, 0.01, contract) >= 0.5
            outcome = 1.0 if resolved_yes else 0.0
            brier_score = (model_prob - outcome) ** 2
        edge = model_prob - market_prob
        trade_recommendation = "NO TRADE"
        if edge >= 0.05:
            trade_recommendation = "BUY YES"
        elif edge <= -0.05:
            trade_recommendation = "BUY NO"
        simulated_trade_pnl = None
        if resolved_yes is not None:
            if trade_recommendation == "BUY YES":
                simulated_trade_pnl = (1.0 if resolved_yes else 0.0) - market_prob
            elif trade_recommendation == "BUY NO":
                simulated_trade_pnl = (1.0 if not resolved_yes else 0.0) - (1.0 - market_prob)
            else:
                simulated_trade_pnl = 0.0
        results.append(
            {
                "ticker": str(contract.get("ticker") or ""),
                "title": str(contract.get("title") or contract.get("subtitle") or ""),
                "rule_family": rule_family,
                "model_yes_probability": round(float(model_prob), 4),
                "market_yes_probability": round(float(market_prob), 4),
                "edge": round(float(edge), 4),
                "trade_recommendation": trade_recommendation,
                "resolved_yes": resolved_yes,
                "brier_score": round(float(brier_score), 4) if brier_score is not None else None,
                "simulated_trade_pnl": round(float(simulated_trade_pnl), 4) if simulated_trade_pnl is not None else None,
            }
        )
    return results


def _summarize_contract_results(contract_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not contract_results:
        return {
            "contract_count": 0,
            "average_brier_score": None,
            "simulated_total_pnl": None,
            "trade_count": 0,
            "win_rate": None,
        }
    brier_scores = [float(item["brier_score"]) for item in contract_results if item.get("brier_score") is not None]
    pnls = [float(item["simulated_trade_pnl"]) for item in contract_results if item.get("simulated_trade_pnl") is not None]
    trade_results = [float(item["simulated_trade_pnl"]) for item in contract_results if item.get("trade_recommendation") != "NO TRADE" and item.get("simulated_trade_pnl") is not None]
    win_rate = None
    if trade_results:
        win_rate = sum(1 for pnl in trade_results if pnl > 0) / len(trade_results)
    return {
        "contract_count": len(contract_results),
        "average_brier_score": round(sum(brier_scores) / len(brier_scores), 4) if brier_scores else None,
        "simulated_total_pnl": round(sum(pnls), 4) if pnls else None,
        "trade_count": len(trade_results),
        "win_rate": round(float(win_rate), 4) if win_rate is not None else None,
    }


def _summarize_contract_results_by_rule_family(contract_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for result in contract_results:
        grouped[str(result.get("rule_family") or "other")].append(result)

    summaries: List[Dict[str, Any]] = []
    for rule_family, items in grouped.items():
        pnls = [float(item["simulated_trade_pnl"]) for item in items if item.get("simulated_trade_pnl") is not None]
        trades = [
            float(item["simulated_trade_pnl"])
            for item in items
            if item.get("trade_recommendation") != "NO TRADE" and item.get("simulated_trade_pnl") is not None
        ]
        brier_scores = [float(item["brier_score"]) for item in items if item.get("brier_score") is not None]
        avg_edge = sum(float(item.get("edge", 0.0)) for item in items) / len(items)
        win_rate = None
        if trades:
            win_rate = sum(1 for pnl in trades if pnl > 0.0) / len(trades)
        summaries.append(
            {
                "rule_family": rule_family,
                "contract_count": len(items),
                "trade_count": len(trades),
                "average_edge": round(float(avg_edge), 4),
                "average_brier_score": round(sum(brier_scores) / len(brier_scores), 4) if brier_scores else None,
                "simulated_total_pnl": round(sum(pnls), 4) if pnls else None,
                "win_rate": round(float(win_rate), 4) if win_rate is not None else None,
            }
        )
    summaries.sort(key=lambda item: item["rule_family"])
    return summaries


def validate_title_signal(
    *,
    title_spec: Dict[str, Any],
    publication_ids: List[str] | None,
    state_backend: str,
    state_root: str,
    sqlite_path: str | None,
    backfill_max_publications: int | None,
    poll_workers: int,
    process_workers: int,
    skip_rt_sync: bool,
    refresh: bool,
) -> Dict[str, Any]:
    title = str(title_spec["title"])
    rt_title_path = title_spec.get("rt_title_path")
    contracts = list(title_spec.get("contracts") or DEFAULT_THRESHOLD_CONTRACTS)

    store = _build_state_store(state_backend, state_root, sqlite_path)
    logger = configure_file_logger(
        "rtKalshiPred.validate_signal",
        str(Path(state_root) / f"{title.replace(' ', '_').lower()}-validation.log"),
        level="INFO",
    )
    engine = RealtimeTomatometerEngine(
        target_title=title,
        publication_ids=publication_ids,
        state_store=store,
        logger=logger,
        poll_workers=poll_workers,
        process_workers=process_workers,
        rt_title_path=rt_title_path,
    )

    if refresh:
        store.delete_title_state(title)
        engine = RealtimeTomatometerEngine(
            target_title=title,
            publication_ids=publication_ids,
            state_store=store,
            logger=logger,
            poll_workers=poll_workers,
            process_workers=process_workers,
            rt_title_path=rt_title_path,
        )
        if not skip_rt_sync:
            engine.sync_rt_baseline()
        engine.backfill_existing_reviews(max_publications=backfill_max_publications)
        engine.poll_once()

    runtime_state = store.load_runtime_state(title)
    snapshot = runtime_state.latest_snapshot
    calculated_score = _coerce_score_percent(snapshot.get("calculated_tomatometer"))
    official_score = _coerce_score_percent(snapshot.get("official_rt_tomatometer"))
    score_error = None
    abs_error = None
    if calculated_score is not None and official_score is not None:
        score_error = calculated_score - official_score
        abs_error = abs(score_error)

    review_count = int(snapshot.get("system_review_count", len(runtime_state.accepted_reviews)))
    score_stdev = _estimate_score_stdev(snapshot, review_count)
    timeline = _review_timeline_metrics(runtime_state.accepted_reviews)
    coverage = _coverage_metrics(snapshot, runtime_state.accepted_reviews)
    contract_results = _evaluate_contracts(calculated_score, official_score, score_stdev, contracts)
    per_publication = _publication_contribution_metrics(runtime_state.accepted_reviews)
    contract_rule_family_summary = _summarize_contract_results_by_rule_family(contract_results)

    return {
        "title": title,
        "rt_title_path": rt_title_path or snapshot.get("official_rt_title_path"),
        "publication_ids": publication_ids or [],
        "calculated_tomatometer": calculated_score,
        "official_rt_tomatometer": official_score,
        "score_error": round(float(score_error), 4) if score_error is not None else None,
        "absolute_score_error": round(float(abs_error), 4) if abs_error is not None else None,
        "system_review_count": review_count,
        "score_stdev": score_stdev,
        "coverage": coverage,
        "timeline": timeline,
        "publication_contributions": per_publication,
        "official_rt_diagnostics": snapshot.get("official_rt_diagnostics", {}),
        "contract_results": contract_results,
        "contract_summary": _summarize_contract_results(contract_results),
        "contract_rule_family_summary": contract_rule_family_summary,
    }


def _aggregate_publication_contributions(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "publication_id": "",
            "outlet_name": None,
            "title_count": 0,
            "review_count": 0,
            "fresh_probability_sum": 0.0,
            "share_of_observed_reviews_sum": 0.0,
            "share_of_expected_freshness_sum": 0.0,
            "appearance_count_for_freshness_share": 0,
            "critic_names": set(),
        }
    )
    for result in results:
        for item in result.get("publication_contributions", []):
            publication_id = str(item.get("publication_id") or "unknown")
            bucket = grouped[publication_id]
            bucket["publication_id"] = publication_id
            bucket["outlet_name"] = item.get("outlet_name") or bucket["outlet_name"]
            bucket["title_count"] += 1
            bucket["review_count"] += int(item.get("review_count", 0))
            bucket["fresh_probability_sum"] += float(item.get("fresh_probability_sum", 0.0) or 0.0)
            bucket["share_of_observed_reviews_sum"] += float(item.get("share_of_observed_reviews", 0.0) or 0.0)
            if item.get("share_of_expected_freshness") is not None:
                bucket["share_of_expected_freshness_sum"] += float(item["share_of_expected_freshness"])
                bucket["appearance_count_for_freshness_share"] += 1
            for critic_name in item.get("critic_names", []):
                if critic_name:
                    bucket["critic_names"].add(str(critic_name))

    aggregated: List[Dict[str, Any]] = []
    for publication_id, bucket in grouped.items():
        title_count = max(int(bucket["title_count"]), 1)
        freshness_share_count = int(bucket["appearance_count_for_freshness_share"])
        aggregated.append(
            {
                "publication_id": publication_id,
                "outlet_name": bucket["outlet_name"],
                "title_count": int(bucket["title_count"]),
                "review_count": int(bucket["review_count"]),
                "average_reviews_per_title": round(int(bucket["review_count"]) / title_count, 4),
                "average_share_of_observed_reviews": round(float(bucket["share_of_observed_reviews_sum"]) / title_count, 4),
                "average_share_of_expected_freshness": round(float(bucket["share_of_expected_freshness_sum"]) / freshness_share_count, 4)
                if freshness_share_count > 0
                else None,
                "fresh_probability_sum": round(float(bucket["fresh_probability_sum"]), 4),
                "critic_count": len(bucket["critic_names"]),
                "critic_names": sorted(bucket["critic_names"]),
            }
        )
    aggregated.sort(key=lambda item: (-int(item["review_count"]), item["publication_id"]))
    return aggregated


def _aggregate_rule_family_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "rule_family": "",
            "contract_count": 0,
            "trade_count": 0,
            "pnl_sum": 0.0,
            "edge_sum": 0.0,
            "edge_count": 0,
            "brier_sum": 0.0,
            "brier_count": 0,
            "winning_trades": 0,
        }
    )
    for result in results:
        for item in result.get("contract_results", []):
            rule_family = str(item.get("rule_family") or "other")
            bucket = grouped[rule_family]
            bucket["rule_family"] = rule_family
            bucket["contract_count"] += 1
            bucket["edge_sum"] += float(item.get("edge", 0.0) or 0.0)
            bucket["edge_count"] += 1
            if item.get("brier_score") is not None:
                bucket["brier_sum"] += float(item["brier_score"])
                bucket["brier_count"] += 1
            if item.get("simulated_trade_pnl") is not None:
                bucket["pnl_sum"] += float(item["simulated_trade_pnl"])
            if item.get("trade_recommendation") != "NO TRADE" and item.get("simulated_trade_pnl") is not None:
                bucket["trade_count"] += 1
                if float(item["simulated_trade_pnl"]) > 0.0:
                    bucket["winning_trades"] += 1

    summaries: List[Dict[str, Any]] = []
    for rule_family, bucket in grouped.items():
        trade_count = int(bucket["trade_count"])
        summaries.append(
            {
                "rule_family": rule_family,
                "contract_count": int(bucket["contract_count"]),
                "trade_count": trade_count,
                "average_edge": round(float(bucket["edge_sum"]) / max(int(bucket["edge_count"]), 1), 4),
                "average_brier_score": round(float(bucket["brier_sum"]) / int(bucket["brier_count"]), 4)
                if int(bucket["brier_count"]) > 0
                else None,
                "simulated_total_pnl": round(float(bucket["pnl_sum"]), 4),
                "win_rate": round(float(bucket["winning_trades"]) / trade_count, 4) if trade_count > 0 else None,
            }
        )
    summaries.sort(key=lambda item: item["rule_family"])
    return summaries


def summarize_validation_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    score_errors = [float(item["absolute_score_error"]) for item in results if item.get("absolute_score_error") is not None]
    coverage_ratios = [float(item["coverage"]["coverage_ratio"]) for item in results if item.get("coverage", {}).get("coverage_ratio") is not None]
    contract_summaries = [item.get("contract_summary", {}) for item in results]
    brier_scores = [float(item["average_brier_score"]) for item in contract_summaries if item.get("average_brier_score") is not None]
    total_pnl = sum(float(item["simulated_total_pnl"]) for item in contract_summaries if item.get("simulated_total_pnl") is not None)
    total_trade_count = sum(int(item["trade_count"]) for item in contract_summaries if item.get("trade_count") is not None)
    timeline_spans = [
        float(item["timeline"]["observed_review_span_hours"])
        for item in results
        if item.get("timeline", {}).get("observed_review_span_hours") is not None
    ]
    interarrival_medians = [
        float(item["timeline"]["median_interarrival_hours"])
        for item in results
        if item.get("timeline", {}).get("median_interarrival_hours") is not None
    ]
    publication_contribution_summary = _aggregate_publication_contributions(results)
    rule_family_summary = _aggregate_rule_family_results(results)

    return {
        "title_count": len(results),
        "titles_with_official_rt": sum(1 for item in results if item.get("official_rt_tomatometer") is not None),
        "mean_absolute_score_error": round(sum(score_errors) / len(score_errors), 4) if score_errors else None,
        "mean_coverage_ratio": round(sum(coverage_ratios) / len(coverage_ratios), 4) if coverage_ratios else None,
        "mean_observed_review_span_hours": round(sum(timeline_spans) / len(timeline_spans), 4) if timeline_spans else None,
        "mean_median_interarrival_hours": round(sum(interarrival_medians) / len(interarrival_medians), 4) if interarrival_medians else None,
        "mean_contract_brier_score": round(sum(brier_scores) / len(brier_scores), 4) if brier_scores else None,
        "simulated_total_pnl": round(float(total_pnl), 4) if total_trade_count or brier_scores else None,
        "simulated_trade_count": total_trade_count,
        "rule_family_summary": rule_family_summary,
        "publication_contribution_summary": publication_contribution_summary[:15],
    }


def build_validation_summary_markdown(report: Dict[str, Any]) -> str:
    summary = dict(report.get("summary", {}))
    results = list(report.get("results", []))
    lines: List[str] = [
        "# RT Signal Validation Summary",
        "",
        "## Batch Summary",
        f"- Titles validated: {summary.get('title_count', 0)}",
        f"- Titles with official RT baseline: {summary.get('titles_with_official_rt', 0)}",
        f"- Mean absolute score error: {summary.get('mean_absolute_score_error')}",
        f"- Mean coverage ratio: {summary.get('mean_coverage_ratio')}",
        f"- Mean contract Brier score: {summary.get('mean_contract_brier_score')}",
        f"- Simulated total P/L: {summary.get('simulated_total_pnl')}",
        f"- Simulated trade count: {summary.get('simulated_trade_count')}",
        "",
        "## Rule Family Performance",
    ]

    for item in summary.get("rule_family_summary", []):
        lines.append(
            f"- `{item['rule_family']}`: contracts={item['contract_count']}, trades={item['trade_count']}, "
            f"avg_edge={item['average_edge']}, avg_brier={item['average_brier_score']}, pnl={item['simulated_total_pnl']}, win_rate={item['win_rate']}"
        )

    lines.extend(["", "## Top Publication Contributors"])
    for item in summary.get("publication_contribution_summary", [])[:10]:
        lines.append(
            f"- `{item['publication_id']}`: titles={item['title_count']}, reviews={item['review_count']}, "
            f"avg_reviews/title={item['average_reviews_per_title']}, avg_review_share={item['average_share_of_observed_reviews']}"
        )

    lines.extend(["", "## Title Highlights"])
    for result in results[:10]:
        lines.append(
            f"- **{result.get('title')}**: predicted={result.get('calculated_tomatometer')}, "
            f"official={result.get('official_rt_tomatometer')}, abs_error={result.get('absolute_score_error')}, "
            f"coverage={result.get('coverage', {}).get('coverage_ratio')}, reviews={result.get('system_review_count')}"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RT signal quality across a batch of titles.")
    parser.add_argument("titles", nargs="*")
    parser.add_argument("--manifest", default=None, help="JSON file with title specs and optional RT paths/contracts.")
    parser.add_argument("--publication-id", action="append", dest="publication_ids")
    parser.add_argument("--publication-preset", choices=sorted(PUBLICATION_PRESETS), default=None)
    parser.add_argument("--state-backend", choices=["filesystem", "sqlite"], default="filesystem")
    parser.add_argument("--state-root", default="data/live_validation_signal")
    parser.add_argument("--sqlite-path", default=None)
    parser.add_argument("--backfill-max-publications", type=int, default=25)
    parser.add_argument("--poll-workers", type=int, default=24)
    parser.add_argument("--process-workers", type=int, default=24)
    parser.add_argument("--skip-rt-sync", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="Delete title state and rerun RT sync/backfill/poll before validating.")
    parser.add_argument("--output", default=None, help="Optional JSON output path for the validation report.")
    parser.add_argument("--summary-output", default=None, help="Optional markdown summary artifact path.")
    args = parser.parse_args()

    title_specs = _load_title_specs(args.manifest, args.titles)
    if not title_specs:
        raise SystemExit("Provide at least one title or a --manifest file.")

    publication_ids = _resolve_publication_ids(args.publication_ids, args.publication_preset)
    results = [
        validate_title_signal(
            title_spec=title_spec,
            publication_ids=publication_ids,
            state_backend=args.state_backend,
            state_root=args.state_root,
            sqlite_path=args.sqlite_path,
            backfill_max_publications=args.backfill_max_publications,
            poll_workers=args.poll_workers,
            process_workers=args.process_workers,
            skip_rt_sync=args.skip_rt_sync,
            refresh=args.refresh,
        )
        for title_spec in title_specs
    ]

    report = {
        "summary": summarize_validation_results(results),
        "results": results,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_markdown = build_validation_summary_markdown(report)
    summary_output = args.summary_output
    if summary_output is None and args.output:
        output_path = Path(args.output)
        summary_output = str(output_path.with_name(f"{output_path.stem}_summary.md"))
    if summary_output:
        Path(summary_output).write_text(summary_markdown, encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

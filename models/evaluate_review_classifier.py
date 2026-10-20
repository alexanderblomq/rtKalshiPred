from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from trainer import DEFAULT_DATASET, build_training_frame, load_jsonl, split_training_frame


DEFAULT_MODEL_PATH = "model_output/review_classifier/model.joblib"


def attach_row_metadata(rows: List[Dict[str, object]]) -> pd.DataFrame:
    metadata_rows: List[Dict[str, object]] = []
    for row in rows:
        fresh_label = row.get("fresh_label")
        if fresh_label not in (0, 1):
            continue
        metadata_rows.append(
            {
                "publication_id": row.get("publication_id") or "",
                "critic_name": row.get("critic_name") or "",
                "headline": row.get("headline") or "",
                "rt_quote": row.get("rt_quote") or "",
                "review_url": row.get("review_url") or "",
                "fresh_label": int(fresh_label),
            }
        )
    return pd.DataFrame(metadata_rows)


def build_error_rows(
    X_test: pd.DataFrame,
    y_test: pd.Series,
    probs,
    preds,
    metadata_test: pd.DataFrame,
) -> List[Dict[str, object]]:
    errors: List[Dict[str, object]] = []
    true_values = y_test.tolist() if hasattr(y_test, "tolist") else list(y_test)
    pred_values = preds.tolist() if hasattr(preds, "tolist") else list(preds)
    prob_values = probs.tolist() if hasattr(probs, "tolist") else list(probs)

    for idx, (true_label, pred_label, prob) in enumerate(zip(true_values, pred_values, prob_values)):
        if true_label == pred_label:
            continue

        meta = metadata_test.iloc[idx]
        errors.append(
            {
                "publication_id": meta["publication_id"],
                "critic_name": meta["critic_name"],
                "headline": meta["headline"],
                "rt_quote": meta["rt_quote"][:240],
                "review_url": meta["review_url"],
                "true_label": int(true_label),
                "predicted_label": int(pred_label),
                "predicted_prob_fresh": float(prob),
                "error_magnitude": float(prob if pred_label == 1 else 1.0 - prob),
                "error_type": "false_positive" if pred_label == 1 else "false_negative",
            }
        )
    return errors


def evaluate(
    dataset_path: str = DEFAULT_DATASET,
    model_path: str = DEFAULT_MODEL_PATH,
    limit: int | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
    top_n: int = 20,
    output_path: str | None = None,
) -> Dict[str, object]:
    rows = load_jsonl(dataset_path, limit=limit)
    frame = build_training_frame(rows)
    metadata = attach_row_metadata(rows)

    X_train, X_test, y_train, y_test = split_training_frame(
        frame,
        test_size=test_size,
        random_state=random_state,
    )
    _, metadata_test = train_test_split(
        metadata,
        test_size=test_size,
        random_state=random_state,
        stratify=metadata["fresh_label"],
    )

    model = joblib.load(model_path)
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    errors = build_error_rows(X_test, y_test, probs, preds, metadata_test.reset_index(drop=True))
    false_positives = sorted(
        [error for error in errors if error["error_type"] == "false_positive"],
        key=lambda item: item["error_magnitude"],
        reverse=True,
    )[:top_n]
    false_negatives = sorted(
        [error for error in errors if error["error_type"] == "false_negative"],
        key=lambda item: item["error_magnitude"],
        reverse=True,
    )[:top_n]

    report = {
        "dataset_path": dataset_path,
        "model_path": model_path,
        "row_count": int(len(frame)),
        "test_rows": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, preds)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
        "classification_report": classification_report(y_test, preds, output_dict=True),
        "top_false_positives": false_positives,
        "top_false_negatives": false_negatives,
    }

    if output_path:
        Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the trained review classifier and print worst errors.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = evaluate(
        dataset_path=args.dataset,
        model_path=args.model,
        limit=args.limit,
        test_size=args.test_size,
        random_state=args.random_state,
        top_n=args.top_n,
        output_path=args.output,
    )

    print(json.dumps({"accuracy": report["accuracy"], "roc_auc": report["roc_auc"], "test_rows": report["test_rows"]}, indent=2))
    print("\nTop False Positives:")
    for row in report["top_false_positives"]:
        print(json.dumps(row, ensure_ascii=True))
    print("\nTop False Negatives:")
    for row in report["top_false_negatives"]:
        print(json.dumps(row, ensure_ascii=True))


if __name__ == "__main__":
    main()

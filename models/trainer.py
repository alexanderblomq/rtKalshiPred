from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from scrapers.base_scraper import resolve_primary_critic_name
from score_normalizer import normalize_score


DEFAULT_DATASET = "data/processed/review_training_dataset_approved_rt_only.jsonl"
DEFAULT_OUTPUT_DIR = "model_output/review_classifier"


def load_jsonl(path: str, limit: int | None = None) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def build_training_frame(rows: List[Dict[str, object]]) -> pd.DataFrame:
    processed: List[Dict[str, object]] = []
    for row in rows:
        fresh_label = row.get("fresh_label")
        if fresh_label not in (0, 1):
            continue

        score_result = normalize_score(row.get("original_score") or row.get("raw_score"))
        combined_text = " \n ".join(
            str(value).strip()
            for value in [
                row.get("headline") or "",
                row.get("rt_quote") or "",
                row.get("body_text") or "",
            ]
            if str(value).strip()
        )

        processed.append(
            {
                "combined_text": combined_text,
                "publication_id": row.get("publication_id") or "",
                "critic_name": resolve_primary_critic_name(
                    critic_name=row.get("critic_name"),
                    critic_names=row.get("critic_names"),
                ),
                "normalized_score": score_result["normalized_score"],
                "fresh_label": int(fresh_label),
            }
        )

    return pd.DataFrame(processed)


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=50000,
                    strip_accents="unicode",
                    sublinear_tf=True,
                ),
                "combined_text",
            ),
            (
                "publication",
                OneHotEncoder(handle_unknown="ignore"),
                ["publication_id"],
            ),
            (
                "critic",
                OneHotEncoder(handle_unknown="ignore"),
                ["critic_name"],
            ),
            (
                "score",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value=-1.0)),
                    ]
                ),
                ["normalized_score"],
            ),
        ],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    solver="liblinear",
                ),
            ),
        ]
    )


def _clip_probabilities(probabilities: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(probabilities, dtype=float), 1e-6, 1.0 - 1e-6)


def _logit_array(probabilities: np.ndarray) -> np.ndarray:
    clipped = _clip_probabilities(probabilities)
    return np.log(clipped / (1.0 - clipped))


def fit_sigmoid_calibrator(probabilities: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    logits = _logit_array(probabilities).reshape(-1, 1)
    model = LogisticRegression(max_iter=1000, solver="lbfgs")
    model.fit(logits, labels)
    return {
        "method": "sigmoid",
        "coef": float(model.coef_[0][0]),
        "intercept": float(model.intercept_[0]),
    }


def apply_sigmoid_calibrator(probabilities: np.ndarray, calibrator: Dict[str, float]) -> np.ndarray:
    logits = _logit_array(probabilities)
    calibrated_logits = (float(calibrator.get("coef", 1.0)) * logits) + float(calibrator.get("intercept", 0.0))
    return 1.0 / (1.0 + np.exp(-calibrated_logits))


def split_training_frame(
    frame: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X = frame[["combined_text", "publication_id", "critic_name", "normalized_score"]]
    y = frame["fresh_label"]

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )


def train_model(
    dataset_path: str = DEFAULT_DATASET,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    limit: int | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, object]:
    rows = load_jsonl(dataset_path, limit=limit)
    frame = build_training_frame(rows)
    if frame.empty:
        raise ValueError("No usable training rows found.")

    X_train, X_test, y_train, y_test = split_training_frame(
        frame,
        test_size=test_size,
        random_state=random_state,
    )

    X_model_train, X_calibration, y_model_train, y_calibration = train_test_split(
        X_train,
        y_train,
        test_size=0.2,
        random_state=random_state,
        stratify=y_train,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_model_train, y_model_train)

    calibration_probs = pipeline.predict_proba(X_calibration)[:, 1]
    calibrator = fit_sigmoid_calibrator(calibration_probs, y_calibration.to_numpy())

    raw_probs = pipeline.predict_proba(X_test)[:, 1]
    probs = apply_sigmoid_calibrator(raw_probs, calibrator)
    preds = (probs >= 0.5).astype(int)

    metrics = {
        "dataset_path": dataset_path,
        "row_count": int(len(frame)),
        "train_rows": int(len(X_train)),
        "model_train_rows": int(len(X_model_train)),
        "calibration_rows": int(len(X_calibration)),
        "test_rows": int(len(X_test)),
        "positive_rows": int(frame["fresh_label"].sum()),
        "negative_rows": int((1 - frame["fresh_label"]).sum()),
        "accuracy": float(accuracy_score(y_test, preds)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
        "raw_roc_auc": float(roc_auc_score(y_test, raw_probs)),
        "calibration": calibrator,
        "classification_report": classification_report(y_test, preds, output_dict=True),
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path / "model.joblib")
    (output_path / "calibration.json").write_text(json.dumps(calibrator, indent=2), encoding="utf-8")
    (output_path / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved trained model to {output_path / 'model.joblib'}")
    print(f"Saved metrics to {output_path / 'metrics.json'}")
    print(json.dumps({k: metrics[k] for k in ['row_count', 'accuracy', 'roc_auc', 'positive_rows', 'negative_rows']}, indent=2))
    return metrics


def train() -> None:
    parser = argparse.ArgumentParser(description="Train a weighted fresh/rotten classifier.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    train_model(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        limit=args.limit,
        test_size=args.test_size,
    )


if __name__ == "__main__":
    train()

"""Reproducible ML training, baseline comparison, and evaluation pipeline."""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.features import CodePatternFeatureExtractor

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATASET_PATH = ROOT_DIR / "datasets" / "type_patterns_dataset.json"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
DOCS_DIR = ROOT_DIR / "docs"


def load_dataset(dataset_path: Path = DATASET_PATH) -> List[Dict[str, Any]]:
    """Load JSON dataset of labeled Python code snippets."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def train_and_evaluate(
    dataset_path: Path = DATASET_PATH,
    artifacts_dir: Path = ARTIFACTS_DIR,
    test_size: float = 0.25,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Train models, evaluate on held-out test set, and persist artifacts."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    records = load_dataset(dataset_path)
    extractor = CodePatternFeatureExtractor()

    # 1. Feature extraction
    X_raw: List[Dict[str, Any]] = [extractor.extract_features(r["code"]) for r in records]
    y_raw: List[str] = [r["target_label"] for r in records]

    # Class balance check
    unique_classes, class_counts = np.unique(y_raw, return_counts=True)
    class_imbalance = {cls: int(cnt) for cls, cnt in zip(unique_classes, class_counts)}

    # 2. Held-out Stratified Split (Split BEFORE vectorizer fitting to prevent leakage)
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(X_raw, y_raw))

    X_train = [X_raw[i] for i in train_idx]
    y_train = [y_raw[i] for i in train_idx]
    X_test = [X_raw[i] for i in test_idx]
    y_test = [y_raw[i] for i in test_idx]

    # 3. Pipelines for Baseline 1 (Logistic Regression) and Baseline 2 (Random Forest)
    pipeline_lr = Pipeline([
        ("vectorizer", DictVectorizer(sparse=False)),
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000, random_state=random_state)),
    ])

    pipeline_rf = Pipeline([
        ("vectorizer", DictVectorizer(sparse=False)),
        ("classifier", RandomForestClassifier(n_estimators=50, max_depth=6, random_state=random_state)),
    ])

    # Fit models on training split only
    pipeline_lr.fit(X_train, y_train)
    pipeline_rf.fit(X_train, y_train)

    # Predictions
    y_pred_lr = pipeline_lr.predict(X_test)
    y_pred_rf = pipeline_rf.predict(X_test)

    # 4. Evaluation Metrics
    classes = sorted(list(set(y_raw)))

    eval_lr = {
        "model": "LogisticRegression",
        "precision_macro": float(precision_score(y_test, y_pred_lr, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, y_pred_lr, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, y_pred_lr, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_test, y_pred_lr, average="weighted", zero_division=0)),
    }

    eval_rf = {
        "model": "RandomForestClassifier",
        "precision_macro": float(precision_score(y_test, y_pred_rf, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, y_pred_rf, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, y_pred_rf, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_test, y_pred_rf, average="weighted", zero_division=0)),
    }

    # Select best model based on macro F1
    best_pipeline = pipeline_rf if eval_rf["f1_macro"] >= eval_lr["f1_macro"] else pipeline_lr
    best_eval = eval_rf if eval_rf["f1_macro"] >= eval_lr["f1_macro"] else eval_lr
    best_y_pred = y_pred_rf if eval_rf["f1_macro"] >= eval_lr["f1_macro"] else y_pred_lr

    # Per-class classification report
    report_dict = classification_report(y_test, best_y_pred, output_dict=True, zero_division=0)
    conf_matrix = confusion_matrix(y_test, best_y_pred, labels=classes).tolist()

    # 5. Persist the chosen model
    model_filename = "type_classifier.joblib"
    model_path = artifacts_dir / model_filename
    joblib.dump(best_pipeline, model_path)

    # Feature names from DictVectorizer
    vectorizer: DictVectorizer = best_pipeline.named_steps["vectorizer"]
    feature_names = vectorizer.get_feature_names_out().tolist()

    metadata: Dict[str, Any] = {
        "model_name": "TypeMind_PatternClassifier",
        "model_version": "1.0.0",
        "model_architecture": best_eval["model"],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_info": {
            "path": str(dataset_path),
            "total_samples": len(records),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "origin": "synthetic",
            "class_imbalance": class_imbalance,
        },
        "training_config": {
            "test_size": test_size,
            "random_state": random_state,
        },
        "features": {
            "count": len(feature_names),
            "names": feature_names,
        },
        "classes": classes,
        "evaluation": {
            "chosen_model": best_eval,
            "baseline_comparison": {
                "LogisticRegression": eval_lr,
                "RandomForestClassifier": eval_rf,
            },
            "per_class_metrics": report_dict,
            "confusion_matrix": {
                "labels": classes,
                "matrix": conf_matrix,
            },
        },
    }

    metadata_path = artifacts_dir / "model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # 6. Generate human-readable Markdown evaluation report
    report_md_path = DOCS_DIR / "ml_evaluation_report.md"
    _write_evaluation_report(metadata, report_md_path)

    print(f"[TypeMind ML] Training completed successfully!")
    print(f"  Chosen Architecture: {best_eval['model']}")
    print(f"  Test F1 (Macro):     {best_eval['f1_macro']:.4f}")
    print(f"  Test F1 (Weighted):  {best_eval['f1_weighted']:.4f}")
    print(f"  Model saved to:      {model_path}")
    print(f"  Metadata saved to:   {metadata_path}")
    print(f"  Report generated:    {report_md_path}")

    return metadata


def _write_evaluation_report(meta: Dict[str, Any], output_path: Path) -> None:
    """Write human-readable Markdown evaluation report."""
    eval_info = meta["evaluation"]
    chosen = eval_info["chosen_model"]
    base_comp = eval_info["baseline_comparison"]
    classes = meta["classes"]
    cm = eval_info["confusion_matrix"]["matrix"]
    per_class = eval_info["per_class_metrics"]

    lines = [
        "# TypeMind AI - Machine Learning Pipeline Evaluation Report",
        "",
        f"**Model Name:** `{meta['model_name']}` (v{meta['model_version']})  ",
        f"**Evaluation Timestamp:** `{meta['trained_at']}`  ",
        f"**Chosen Architecture:** `{chosen['model']}`  ",
        "",
        "> [!IMPORTANT]",
        "> **Dataset Origin & Limitations:**",
        f"> The evaluation was conducted on `{meta['dataset_info']['total_samples']}` synthetically authored Python code patterns.",
        "> This synthetic benchmark confirms reproducible pipeline mechanics, abstract feature vectorization, and model persistence.",
        "> It does **not** represent real-world software project distribution.",
        "",
        "---",
        "",
        "## 1. Baseline Model Comparison",
        "",
        "| Architecture | Precision (Macro) | Recall (Macro) | F1-Score (Macro) | F1-Score (Weighted) |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for model_name, m in base_comp.items():
        lines.append(
            f"| **{model_name}** | {m['precision_macro']:.4f} | {m['recall_macro']:.4f} | {m['f1_macro']:.4f} | {m['f1_weighted']:.4f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Per-Class Test Performance",
        "",
        "| Class / Target Label | Precision | Recall | F1-Score | Support |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ])

    for c in classes:
        if c in per_class:
            stats = per_class[c]
            lines.append(
                f"| `{c}` | {stats['precision']:.4f} | {stats['recall']:.4f} | {stats['f1-score']:.4f} | {int(stats['support'])} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Confusion Matrix",
        "",
        "Row = Ground Truth, Column = Predicted",
        "",
        "| Ground Truth \\ Predicted | " + " | ".join(f"`{c}`" for c in classes) + " |",
        "| :--- | " + " | ".join(":---:" for _ in classes) + " |",
    ])

    for i, row_label in enumerate(classes):
        row_str = " | ".join(str(cm[i][j]) for j in range(len(classes)))
        lines.append(f"| **`{row_label}`** | {row_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Dataset Class Distribution",
        "",
        "| Class | Sample Count | Percentage |",
        "| :--- | :--- | :--- |",
    ])

    total_s = meta["dataset_info"]["total_samples"]
    for c, cnt in meta["dataset_info"]["class_imbalance"].items():
        pct = (cnt / total_s) * 100.0
        lines.append(f"| `{c}` | {cnt} | {pct:.1f}% |")

    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    train_and_evaluate()

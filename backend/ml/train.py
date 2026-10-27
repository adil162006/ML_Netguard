import json
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

from .config import (ARTIFACT_FILE, COMPARISON_FILE, FEATURES, METRICS_FILE,
                     MODEL_DIR, NUMERICAL, RANDOM_STATE, REPORT_DIR, TEST_FILE,
                     TRAIN_FILE)
from .preprocess import make_preprocessor


def load_dataset(path):
    if not path.exists():
        raise FileNotFoundError(f"Required dataset is missing: {path.name}. Place it in backend/data.")
    header = pd.read_csv(path, nrows=0).columns
    missing = sorted(set(FEATURES + ["label"]) - set(header))
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {', '.join(missing)}")
    data = pd.read_csv(path, usecols=FEATURES + ["label"], low_memory=False)
    if "attack_cat" in header:
        labels = pd.read_csv(path, usecols=["label", "attack_cat"], low_memory=False)
        normal_mismatch = (labels.label == 0) & (labels.attack_cat.astype(str).str.casefold() != "normal")
        attack_mismatch = (labels.label == 1) & (labels.attack_cat.astype(str).str.casefold() == "normal")
        if normal_mismatch.any() or attack_mismatch.any():
            raise ValueError(f"{path.name} does not consistently map label 0 to Normal and label 1 to Attack.")
    return data


def run_training():
    train, test = load_dataset(TRAIN_FILE), load_dataset(TEST_FILE)
    for frame, name in ((train, "training"), (test, "testing")):
        if not set(frame.label.dropna().unique()).issubset({0, 1}):
            raise ValueError(f"{name} label must use 0=Normal and 1=Attack.")
        frame["label"] = frame.label.astype(int)
    X_train, y_train = train[FEATURES], train.label
    X_test, y_test = test[FEATURES], test.label
    print(f"Training records: {len(train):,}; testing records: {len(test):,}; selected features: {len(FEATURES)}")
    print("Missing values (training):", train[FEATURES].isna().sum().to_dict())
    print("Missing values (testing):", test[FEATURES].isna().sum().to_dict())
    print("Training target counts:", y_train.value_counts().sort_index().to_dict())
    print("Testing target counts:", y_test.value_counts().sort_index().to_dict())
    print("Categorical cardinality:", {c: int(train[c].nunique()) for c in ("proto", "service")})

    models = {
        "Logistic Regression": (LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE), True),
        "K-Nearest Neighbors": (KNeighborsClassifier(n_neighbors=5, weights="distance", algorithm="brute", n_jobs=-1), True),
        "Decision Tree": (DecisionTreeClassifier(class_weight="balanced", random_state=RANDOM_STATE, min_samples_leaf=2), False),
    }
    results, candidates = {}, {}
    for name, (estimator, scale) in models.items():
        print(f"Training {name}...", flush=True)
        pipeline = Pipeline([("preprocessor", make_preprocessor(scale)), ("classifier", estimator)])
        start = time.perf_counter(); pipeline.fit(X_train, y_train); fit_seconds = time.perf_counter() - start
        start = time.perf_counter(); pred = pipeline.predict(X_test); predict_seconds = time.perf_counter() - start
        probabilities = pipeline.predict_proba(X_test) if hasattr(pipeline, "predict_proba") else None
        matrix = confusion_matrix(y_test, pred, labels=[0, 1])
        metrics = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision": float(precision_score(y_test, pred, pos_label=1, zero_division=0)),
            "recall": float(recall_score(y_test, pred, pos_label=1, zero_division=0)),
            "f1": float(f1_score(y_test, pred, pos_label=1, zero_division=0)),
            "confusion_matrix": matrix.tolist(),
            "classification_report": classification_report(y_test, pred, labels=[0, 1], target_names=["Normal", "Attack"], output_dict=True, zero_division=0),
            "training_seconds": fit_seconds, "prediction_seconds": predict_seconds,
        }
        results[name] = metrics
        candidates[name] = {"pipeline": pipeline, "probabilities": probabilities}
        print(f"{name}: accuracy={metrics['accuracy']:.4f}, attack recall={metrics['recall']:.4f}, attack F1={metrics['f1']:.4f}; train={fit_seconds:.2f}s predict={predict_seconds:.2f}s", flush=True)

    selected = max(results, key=lambda n: (results[n]["recall"], results[n]["f1"], results[n]["precision"], results[n]["accuracy"]))
    metadata = {
        "selected_model": selected,
        "selection_criteria": "Highest Attack-class recall, then Attack-class F1, precision, and accuracy (lexicographic).",
        "feature_names": FEATURES,
        "feature_count": len(FEATURES),
        "target_mapping": {"0": "Normal", "1": "Attack"},
        "dataset": {"name": "UNSW-NB15", "training_records": len(train), "testing_records": len(test),
                    "training_class_counts": {str(k): int(v) for k,v in y_train.value_counts().sort_index().items()},
                    "testing_class_counts": {str(k): int(v) for k,v in y_test.value_counts().sort_index().items()},
                    "missing_values_training": {k: int(v) for k,v in train[FEATURES].isna().sum().items()},
                    "missing_values_testing": {k: int(v) for k,v in test[FEATURES].isna().sum().items()},
                    "categorical_cardinality": {c: int(train[c].nunique()) for c in ("proto", "service")}},
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "models": results,
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True); REPORT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": candidates[selected]["pipeline"], "metadata": metadata}, ARTIFACT_FILE, compress=3)
    METRICS_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    pd.DataFrame([{"algorithm": n, **{k: v for k,v in m.items() if k in ("accuracy", "precision", "recall", "f1", "training_seconds", "prediction_seconds")}, "selected": n == selected} for n,m in results.items()]).to_csv(COMPARISON_FILE, index=False)
    print(f"Selected model: {selected}")
    return metadata


if __name__ == "__main__":
    run_training()

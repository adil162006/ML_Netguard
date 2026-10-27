import json
import joblib
from ml.config import ARTIFACT_FILE, METRICS_FILE

model = None
metadata = None
load_error = None


def load_model():
    global model, metadata, load_error
    if not ARTIFACT_FILE.exists():
        model, metadata = None, None
        load_error = "Model artifact is missing. Train the models with `python -m ml.train` from backend/."
        return
    try:
        package = joblib.load(ARTIFACT_FILE)
        model, metadata = package["model"], package["metadata"]
        if METRICS_FILE.exists():
            metadata = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
        load_error = None
    except Exception:
        model, metadata = None, None
        load_error = "The saved model could not be loaded. Retrain the models and try again."

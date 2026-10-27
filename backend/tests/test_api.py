import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Starlette 0.36 passes an `app` keyword removed by httpx 0.28. Keep these
# endpoint tests runnable in environments that already have that combination.
import httpx
if "app" not in __import__("inspect").signature(httpx.Client.__init__).parameters:
    _httpx_client_init = httpx.Client.__init__
    def _compatible_httpx_init(self, *args, app=None, **kwargs):
        return _httpx_client_init(self, *args, **kwargs)
    httpx.Client.__init__ = _compatible_httpx_init

from fastapi.testclient import TestClient
from app.main import app
from app.services import model_loader

VALID = {"dur": 0.12, "proto": "tcp", "service": "http", "sbytes": 1000, "dbytes": 500,
         "spkts": 10, "dpkts": 8, "sttl": 64, "dttl": 252, "ct_srv_src": 2}


def test_health_and_untrained_metadata(monkeypatch):
    def absent():
        model_loader.model, model_loader.metadata = None, None
        model_loader.load_error = "Missing model"
    monkeypatch.setattr(model_loader, "load_model", absent)
    with TestClient(app) as client:
        assert client.get("/health").json()["model_loaded"] is False
        assert client.get("/api/model-info").status_code == 503
        assert client.get("/api/metrics").status_code == 503


def test_prediction_validation_errors(monkeypatch):
    def absent():
        model_loader.model, model_loader.metadata = None, None
        model_loader.load_error = "Missing model"
    monkeypatch.setattr(model_loader, "load_model", absent)
    with TestClient(app) as client:
        assert client.post("/api/predict", json={}).status_code == 422
        invalid = {**VALID, "dur": "not-a-number"}
        assert client.post("/api/predict", json=invalid).status_code == 422
        extra = {**VALID, "label": 1}
        assert client.post("/api/predict", json=extra).status_code == 422


def test_batch_validates_rows_and_caps_size(monkeypatch):
    class FakeModel:
        classes_ = [0, 1]
        def predict(self, frame): return [1]
        def predict_proba(self, frame): return [[0.2, 0.8]]
    metadata = {"selected_model": "Test Model", "feature_count": 10, "feature_names": list(VALID),
                "dataset": {}, "trained_at_utc": "test", "models": {}, "selection_criteria": "test"}
    def available():
        model_loader.model, model_loader.metadata, model_loader.load_error = FakeModel(), metadata, None
    monkeypatch.setattr(model_loader, "load_model", available)
    with TestClient(app) as client:
        assert client.get("/health").json()["model_loaded"] is True
        assert client.get("/api/model-info").status_code == 200
        assert client.get("/api/metrics").status_code == 200
        single = client.post("/api/predict", json=VALID)
        assert single.status_code == 200
        assert single.json()["label"] == 1 and single.json()["class_name"] == "Attack"
        assert set(single.json()["probabilities"]) == {"0", "1"}
        result = client.post("/api/predict-batch", json={"records": [{}, VALID]})
        assert result.status_code == 200
        assert [row["ok"] for row in result.json()["results"]] == [False, True]
        assert client.post("/api/predict-batch", json={"records": [{}] * 101}).status_code == 422


def test_saved_artifact_predicts_real_record():
    model_loader.load_model()
    if model_loader.model is None:
        import pytest
        pytest.skip("Train the model first to run the saved-artifact integration check")
    with TestClient(app) as client:
        response = client.post("/api/predict", json=VALID)
        assert response.status_code == 200
        assert response.json()["class_name"] in {"Normal", "Attack"}
        assert response.json()["model"] == model_loader.metadata["selected_model"]
        assert len(model_loader.metadata["feature_names"]) == 10

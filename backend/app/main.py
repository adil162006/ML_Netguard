from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .schemas import BatchRequest, TrafficRecord
from .services import model_loader
from .services.prediction import predict_record


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_loader.load_model()
    yield


app = FastAPI(title="NetGuard API", description="UNSW-NB15 traffic record classification API.", version="1.0.0", lifespan=lifespan)
origins = [origin.strip() for origin in os.getenv("NETGUARD_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/")
def root():
    return {"message": "NetGuard API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model_loader.model is not None, "message": model_loader.load_error}


@app.get("/api/model-info")
def model_info():
    if model_loader.metadata is None:
        raise HTTPException(503, detail=model_loader.load_error or "Model metadata is unavailable.")
    return {k: model_loader.metadata[k] for k in ("selected_model", "feature_count", "feature_names", "dataset", "trained_at_utc", "models", "selection_criteria")}


@app.get("/api/metrics")
def metrics():
    if model_loader.metadata is None:
        raise HTTPException(503, detail=model_loader.load_error or "Model metrics are unavailable.")
    return {"selected_model": model_loader.metadata["selected_model"], "selection_criteria": model_loader.metadata["selection_criteria"], "models": model_loader.metadata["models"]}


@app.post("/api/predict")
def predict(record: TrafficRecord):
    try:
        return predict_record(record)
    except RuntimeError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail="Prediction failed. Check the submitted values and model setup.") from exc


@app.post("/api/predict-batch")
def predict_batch(request: BatchRequest):
    if not request.records:
        raise HTTPException(422, detail="records must contain at least one item.")
    if len(request.records) > 100:
        raise HTTPException(422, detail="Batch size cannot exceed 100 records.")
    results = []
    for index, row in enumerate(request.records):
        try:
            record = TrafficRecord.model_validate(row)
            results.append({"index": index, "ok": True, "prediction": predict_record(record)})
        except ValidationError as exc:
            results.append({"index": index, "ok": False, "errors": [{"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]} for err in exc.errors()]})
        except RuntimeError as exc:
            raise HTTPException(503, detail=str(exc)) from exc
    return {"results": results, "count": len(results)}

import pandas as pd
from ..schemas import TrafficRecord
from . import model_loader


def predict_record(record: TrafficRecord):
    if model_loader.model is None:
        raise RuntimeError("The trained model is not available. Train the models before making predictions.")
    frame = pd.DataFrame([record.model_dump()])
    predicted = int(model_loader.model.predict(frame)[0])
    response = {
        "label": predicted,
        "class_name": "Attack" if predicted == 1 else "Normal",
        "model": model_loader.metadata["selected_model"],
        "probabilities": None,
        "explanation": "This is a machine-learning prediction from the submitted record, not a guarantee of security.",
    }
    if hasattr(model_loader.model, "predict_proba"):
        values = model_loader.model.predict_proba(frame)[0]
        response["probabilities"] = {str(int(c)): float(values[i]) for i, c in enumerate(model_loader.model.classes_)}
    return response

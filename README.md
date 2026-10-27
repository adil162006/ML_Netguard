# NetGuard — Machine Learning-Based Network Intrusion Detection

NetGuard is a local college project that classifies submitted network flow records as **Normal (0)** or **Attack (1)**. It trains three scikit-learn baselines on the official UNSW-NB15 training CSV, evaluates them on the official testing CSV, saves the selected pipeline and actual metrics, and provides a FastAPI backend with a React dashboard.

> This application classifies records submitted by a user. It does not capture packets or monitor live network traffic.

## Project contents

- Leakage-safe preprocessing and training scripts for Logistic Regression, KNN and Decision Tree.
- Attack-class precision, recall and F1, overall accuracy, classification reports, confusion matrices, and timing.
- Selection by attack recall, followed by attack F1, precision and accuracy.
- FastAPI endpoints for health, model information, metrics, single predictions, and batch predictions.
- Responsive React dashboard with overview, traffic analysis, model performance and project details.
- The trained model and reports are generated locally and excluded from Git.

## Dataset

Download the official `UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv` from the [UNSW-NB15 dataset page](https://research.unsw.edu.au/projects/unsw-nb15-dataset). Put both files here:

```text
backend/data/UNSW_NB15_training-set.csv
backend/data/UNSW_NB15_testing-set.csv
```

The supplied dataset files are already in that location in this workspace. The script validates required columns and the binary target convention. It does not combine or randomly split the predefined files.

Exactly these features are used, in API order:

`dur`, `proto`, `service`, `sbytes`, `dbytes`, `spkts`, `dpkts`, `sttl`, `dttl`, `ct_srv_src`

`label` is the target (`0` Normal, `1` Attack); `attack_cat`, `id`, and all other columns are excluded. Numerical missing values use training medians; categorical missing values use training modes. `proto` and `service` are one-hot encoded with unknown categories ignored. Logistic Regression and KNN scale numeric values; Decision Tree uses the same categorical encoding and unscaled numeric values. Each transform is fitted only on the training split.

## Prerequisites

- Windows 10/11 and PowerShell
- Python 3.10–3.13
- Node.js 20+ and npm
- The two UNSW-NB15 CSV files

## Run locally

### 1. Install backend dependencies and train

```powershell
cd C:\Users\awwab\Desktop\ML-NetGuard\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ml.train
```

If PowerShell blocks activation, allow it for this terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Training reports row counts, missing values and class distributions before fitting. It evaluates all rows in the provided testing file and writes:

- `backend/models/netguard_model.joblib` — selected preprocessing and model pipeline with metadata.
- `backend/reports/metrics.json` — complete reports, confusion matrices, timings and metadata for each model.
- `backend/reports/model_comparison.csv` — compact comparison table.

Run `python -m ml.train` again after replacing either dataset file to retrain. KNN evaluation can take materially longer than fitting the other two models because exact nearest-neighbor prediction compares each test row against the training records.

### 2. Start the backend

In the activated backend terminal:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend: <http://127.0.0.1:8000> · Swagger UI: <http://127.0.0.1:8000/docs>

The backend does not train on startup. Optional CORS origins can be configured in `backend/.env.example`; by default only localhost and 127.0.0.1 Vite development origins are allowed. Set `NETGUARD_CORS_ORIGINS` in the process environment when you need a different local origin.

### 3. Start the frontend

Open another PowerShell terminal:

```powershell
cd C:\Users\awwab\Desktop\ML-NetGuard\frontend
npm install
npm run dev
```

Frontend: <http://127.0.0.1:5174>. To change the API URL, copy `.env.example` to `.env.local`, edit `VITE_API_URL`, then restart Vite.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API status |
| GET | `/health` | API and model load status |
| GET | `/api/model-info` | Selected model, feature order, dataset metadata and metrics |
| GET | `/api/metrics` | Comparison data for all three models |
| POST | `/api/predict` | Classify one record |
| POST | `/api/predict-batch` | Classify up to 100 rows; reports invalid rows individually |

Example request (illustrative only):

```powershell
$record = @{
  dur = 0.12; proto = "tcp"; service = "http"; sbytes = 1000; dbytes = 500
  spkts = 10; dpkts = 8; sttl = 64; dttl = 252; ct_srv_src = 2
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/predict -ContentType "application/json" -Body $record
```

The response includes the integer class, class name, model name, class probabilities when supported, and a model-prediction limitation statement. Probabilities are not presented as calibrated confidence. Input numbers must be finite and non-negative, categorical strings must be non-empty, missing fields and extra fields are rejected.

## Testing and checks

From `backend/` with dependencies installed:

```powershell
python -m pytest -q
```

From `frontend/` after `npm install`:

```powershell
npm test
npm run build
```

The backend tests cover health and missing-artifact behavior, API validation, dataset schemas and label mapping, batch size validation, and a prediction using the saved artifact. Frontend tests cover dashboard rendering, navigation, required field validation, prediction display, and API errors.

## Measured results

The checked-in workspace reports below came from the supplied 82,332-row training split and 175,341-row testing split. Precision, recall and F1 are for the Attack class. Confusion matrix order is `[[TN, FP], [FN, TP]]`.

| Algorithm | Accuracy | Attack precision | Attack recall | Attack F1 | Confusion matrix |
|---|---:|---:|---:|---:|---|
| Logistic Regression | 79.41% | 97.98% | 71.22% | 82.48% | `[[54250, 1750], [34349, 84992]]` |
| K-Nearest Neighbors | 89.66% | 97.19% | 87.34% | 92.00% | `[[52991, 3009], [15113, 104228]]` |
| Decision Tree (selected) | 90.73% | 97.54% | 88.62% | 92.86% | `[[53329, 2671], [13581, 105760]]` |

Decision Tree is selected by the specified ordering: Attack recall first, then Attack F1, precision and accuracy. The full timing and classification reports are stored in `backend/reports/metrics.json`; KNN prediction took about 547 seconds in this run.

For a built frontend bundle:

```powershell
cd ..\frontend
npm run build
```

Training itself performs dataset schema/label checks and fits/saves the model before the API loads it. The test set is used only for evaluation, not fitting or tuning.

## Metrics guide

- **Accuracy**: share of all test records classified correctly.
- **Precision (Attack)**: among records predicted as attacks, the share that are attacks.
- **Recall (Attack)**: among actual attacks, the share detected. Missed attacks reduce this value.
- **F1 (Attack)**: harmonic mean of attack precision and recall.
- **Confusion matrix**: rows are actual class (`Normal`, `Attack`), columns are predicted class in that same order: `[[TN, FP], [FN, TP]]`.

The comparison and chosen model are derived from measured test-set outputs. Metrics may vary if the dataset version or scikit-learn version changes.

## Troubleshooting

- **Dataset missing / required columns missing:** verify both official CSV filenames and their location under `backend/data/`.
- **Model is unavailable / API returns 503:** activate the backend environment, run `python -m ml.train` from `backend/`, then restart Uvicorn.
- **CORS error:** use the configured Vite URL or set `NETGUARD_CORS_ORIGINS` before launching Uvicorn.
- **Frontend cannot connect:** confirm Uvicorn is on port 8000 and `VITE_API_URL` matches it.
- **Slow training:** exact KNN evaluation is the main cost; let it finish and avoid starting multiple training jobs at once.
- **Activation blocked:** use the process-scoped PowerShell execution-policy command above.

## Limitations and future work

This is a supervised classifier over ten selected UNSW-NB15 fields, not an inline network defense product. It does not capture live traffic, block connections, guarantee safety, calibrate output probabilities, or establish performance on networks beyond the dataset. Possible future work includes calibration, threshold analysis, additional datasets, drift evaluation and packet ingestion with appropriate safeguards.

## Folder structure

```text
backend/  FastAPI service, ML scripts, data, generated models and reports, tests
frontend/ Vite React dashboard, API client, pages and styling
README.md Setup, evaluation, API and troubleshooting guide
```

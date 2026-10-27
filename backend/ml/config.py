from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
TRAIN_FILE = DATA_DIR / "UNSW_NB15_training-set.csv"
TEST_FILE = DATA_DIR / "UNSW_NB15_testing-set.csv"
ARTIFACT_FILE = MODEL_DIR / "netguard_model.joblib"
METRICS_FILE = REPORT_DIR / "metrics.json"
COMPARISON_FILE = REPORT_DIR / "model_comparison.csv"
FEATURES = ["dur", "proto", "service", "sbytes", "dbytes", "spkts", "dpkts", "sttl", "dttl", "ct_srv_src"]
CATEGORICAL = ["proto", "service"]
NUMERICAL = [name for name in FEATURES if name not in CATEGORICAL]
RANDOM_STATE = 42

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.config import FEATURES, TEST_FILE, TRAIN_FILE
from ml.train import load_dataset


def test_official_splits_have_required_features_and_binary_mapping():
    for path in (TRAIN_FILE, TEST_FILE):
        frame = load_dataset(path)
        assert all(feature in frame.columns for feature in FEATURES)
        assert "label" in frame.columns
        assert set(frame.label.unique()) == {0, 1}
        assert "attack_cat" not in frame.columns
        assert "id" not in frame.columns


def test_api_feature_order_excludes_targets():
    assert FEATURES == ["dur", "proto", "service", "sbytes", "dbytes", "spkts", "dpkts", "sttl", "dttl", "ct_srv_src"]
    assert "label" not in FEATURES and "attack_cat" not in FEATURES and "id" not in FEATURES

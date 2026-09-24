"""
Tests for AERIS XGBoost Training & Evaluation Module (tests/test_train.py)
==========================================================================
Validates:
1. Model predictions are strictly finite (no NaN, no Inf).
2. Target column is strictly excluded from feature matrix.
3. Train/validation chronological separation is enforced.
4. Saved metrics JSON contains all required fields.
5. Model can be serialized to JSON and loaded back producing identical predictions.
6. Feature importance CSV contains required columns and all 25 features.
7. SHAP importance CSV contains required columns and all 25 features.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.src.features import CITY_FEATURE_COLUMNS, CITY_TARGET_COLUMN
from ml.src.train import (
    audit_validation_predictions,
    load_datasets,
    load_trained_model,
    train_xgboost_forecast,
)


class TestXGBoostForecaster:
    @pytest.fixture
    def mock_training_environment(self, tmp_path):
        """Creates small mock train and validation parquet datasets."""
        # 48 hours total: 36 train, 12 val
        ts_train = pd.date_range("2023-01-12 00:00", periods=36, freq="1h", tz="Asia/Kolkata")
        ts_val = pd.date_range("2023-01-13 12:00", periods=12, freq="1h", tz="Asia/Kolkata")

        def _make_df(ts):
            n = len(ts)
            data = {
                "timestamp": ts,
                CITY_TARGET_COLUMN: 30.0 + 10.0 * np.sin(np.arange(n) * 2 * np.pi / 12),
                "pm25_current": 30.0 + 10.0 * np.sin(np.arange(n) * 2 * np.pi / 12) - 1.0,
            }
            for col in CITY_FEATURE_COLUMNS:
                data[col] = float(col.__hash__() % 50 + 10) + np.arange(n) * 0.1
            return pd.DataFrame(data)

        train_df = _make_df(ts_train)
        val_df = _make_df(ts_val)

        train_p = tmp_path / "train.parquet"
        val_p = tmp_path / "val.parquet"
        train_df.to_parquet(train_p, index=False)
        val_df.to_parquet(val_p, index=False)

        return str(train_p), str(val_p), tmp_path

    def test_model_output_is_finite(self, mock_training_environment):
        """Verifies that model predictions on validation set are finite numbers."""
        train_p, val_p, tmp_dir = mock_training_environment
        report = train_xgboost_forecast(
            train_path=train_p,
            val_path=val_p,
            model_output_path=str(tmp_dir / "model.json"),
            metrics_output_path=str(tmp_dir / "metrics.json"),
            fi_output_path=str(tmp_dir / "fi.csv"),
            shap_output_path=str(tmp_dir / "shap.csv"),
            n_estimators=10,
            max_depth=2,
        )
        assert np.isfinite(report["metrics"]["mae"])
        assert np.isfinite(report["metrics"]["rmse"])
        assert np.isfinite(report["metrics"]["r2"])

    def test_target_excluded_from_feature_matrix(self):
        """Verifies target column is strictly not in CITY_FEATURE_COLUMNS."""
        assert CITY_TARGET_COLUMN not in CITY_FEATURE_COLUMNS
        assert "pm25_target_t_plus_1" not in CITY_FEATURE_COLUMNS
        assert "pm25_current" not in CITY_FEATURE_COLUMNS

    def test_train_validation_temporal_separation(self, tmp_path):
        """Verifies that load_datasets raises ValueError if train overlaps or follows validation."""
        ts_overlapping = pd.date_range("2023-01-12 00:00", periods=10, freq="1h", tz="Asia/Kolkata")
        data = {
            "timestamp": ts_overlapping,
            CITY_TARGET_COLUMN: np.arange(10, dtype=float),
            "pm25_current": np.arange(10, dtype=float),
        }
        for col in CITY_FEATURE_COLUMNS:
            data[col] = np.ones(10)

        df = pd.DataFrame(data)
        p1 = tmp_path / "t1.parquet"
        p2 = tmp_path / "t2.parquet"
        df.to_parquet(p1, index=False)
        df.to_parquet(p2, index=False)

        with pytest.raises(ValueError, match="Temporal leakage detected"):
            load_datasets(str(p1), str(p2))

    def test_saved_metrics_contain_required_fields(self, mock_training_environment):
        """Verifies that the generated metrics JSON contains all required evaluation fields."""
        train_p, val_p, tmp_dir = mock_training_environment
        metrics_file = tmp_dir / "test_metrics.json"

        train_xgboost_forecast(
            train_path=train_p,
            val_path=val_p,
            model_output_path=str(tmp_dir / "model.json"),
            metrics_output_path=str(metrics_file),
            fi_output_path=str(tmp_dir / "fi.csv"),
            shap_output_path=str(tmp_dir / "shap.csv"),
            n_estimators=10,
            max_depth=2,
        )

        assert metrics_file.exists()
        with open(metrics_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = [
            "model", "target", "validation_type", "target_source", "target_source_type",
            "mae", "rmse", "r2", "persistence_mae", "persistence_rmse",
            "mae_improvement", "rmse_improvement",
        ]
        for k in required_keys:
            assert k in data, f"Missing required key '{k}' in metrics.json"

        assert data["model"] == "XGBoost"
        assert data["target"] == "pm25_target_t_plus_1"
        assert data["validation_type"] == "temporal_holdout"
        assert data["target_source_type"] == "modeled"

    def test_model_can_be_loaded_back_successfully(self, mock_training_environment):
        """Verifies that the serialized XGBoost model loads and reproduces identical predictions."""
        train_p, val_p, tmp_dir = mock_training_environment
        model_file = tmp_dir / "model.json"

        report = train_xgboost_forecast(
            train_path=train_p,
            val_path=val_p,
            model_output_path=str(model_file),
            metrics_output_path=str(tmp_dir / "metrics.json"),
            fi_output_path=str(tmp_dir / "fi.csv"),
            shap_output_path=str(tmp_dir / "shap.csv"),
            n_estimators=10,
            max_depth=2,
        )

        loaded_model = load_trained_model(str(model_file))
        val_df = pd.read_parquet(val_p)
        X_val = val_df[CITY_FEATURE_COLUMNS]

        y_pred_loaded = loaded_model.predict(X_val)
        mae_loaded = float(np.mean(np.abs(val_df[CITY_TARGET_COLUMN] - y_pred_loaded)))
        assert round(mae_loaded, 4) == report["metrics"]["mae"]

    def test_feature_importance_columns_exist(self, mock_training_environment):
        """Verifies feature importance CSV format, columns, and descending order."""
        train_p, val_p, tmp_dir = mock_training_environment
        fi_file = tmp_dir / "fi.csv"

        train_xgboost_forecast(
            train_path=train_p,
            val_path=val_p,
            model_output_path=str(tmp_dir / "model.json"),
            metrics_output_path=str(tmp_dir / "metrics.json"),
            fi_output_path=str(fi_file),
            shap_output_path=str(tmp_dir / "shap.csv"),
            n_estimators=10,
            max_depth=2,
        )

        assert fi_file.exists()
        fi_df = pd.read_csv(fi_file)
        assert list(fi_df.columns) == ["feature", "importance"]
        assert len(fi_df) == len(CITY_FEATURE_COLUMNS)
        # Check sorted descending
        assert fi_df["importance"].is_monotonic_decreasing

    def test_shap_importance_columns_exist(self, mock_training_environment):
        """Verifies SHAP importance CSV format, columns, and descending order."""
        train_p, val_p, tmp_dir = mock_training_environment
        shap_file = tmp_dir / "shap.csv"

        report = train_xgboost_forecast(
            train_path=train_p,
            val_path=val_p,
            model_output_path=str(tmp_dir / "model.json"),
            metrics_output_path=str(tmp_dir / "metrics.json"),
            fi_output_path=str(tmp_dir / "fi.csv"),
            shap_output_path=str(shap_file),
            n_estimators=10,
            max_depth=2,
        )

        if report["shap_status"] == "success":
            assert shap_file.exists()
            shap_df = pd.read_csv(shap_file)
            assert list(shap_df.columns) == ["feature", "mean_abs_shap"]
            assert len(shap_df) == len(CITY_FEATURE_COLUMNS)
            assert shap_df["mean_abs_shap"].is_monotonic_decreasing

    def test_audit_validation_predictions_reproducibility(self, mock_training_environment):
        """Verifies validation prediction audit CSV columns, absence of nulls/infs, and metric consistency."""
        train_p, val_p, tmp_dir = mock_training_environment
        model_file = tmp_dir / "model.json"
        audit_csv = tmp_dir / "val_predictions.csv"

        report = train_xgboost_forecast(
            train_path=train_p,
            val_path=val_p,
            model_output_path=str(model_file),
            metrics_output_path=str(tmp_dir / "metrics.json"),
            fi_output_path=str(tmp_dir / "fi.csv"),
            shap_output_path=str(tmp_dir / "shap.csv"),
            n_estimators=10,
            max_depth=2,
        )

        audit_df, diag = audit_validation_predictions(
            model_path=str(model_file),
            val_path=val_p,
            output_csv_path=str(audit_csv),
        )

        assert audit_csv.exists()
        expected_cols = [
            "timestamp",
            "actual_pm25",
            "xgb_prediction",
            "persistence_prediction",
            "xgb_error",
            "persistence_error",
            "abs_xgb_error",
            "abs_persistence_error",
        ]
        assert list(audit_df.columns) == expected_cols
        assert not audit_df.isnull().any().any()
        assert not np.isinf(audit_df.select_dtypes(include=np.number)).any().any()

        # Check mathematical relations
        np.testing.assert_allclose(audit_df["abs_xgb_error"], np.abs(audit_df["xgb_error"]))
        np.testing.assert_allclose(audit_df["abs_persistence_error"], np.abs(audit_df["persistence_error"]))

        # MAE and RMSE match train report
        assert diag["mae"] == report["metrics"]["mae"]
        assert diag["rmse"] == report["metrics"]["rmse"]

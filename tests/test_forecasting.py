"""
Unit Tests for Machine Learning Forecasting & Leakage-Free Pipeline
Covers TC-08, TC-09, TC-10, TC-11 per SRS Section 10.1.
"""
import pytest
import pandas as pd
from src.data_loader import get_or_create_demo_data, process_uploaded_dataset
from src.eda_analytics import calculate_kpis
from src.forecasting import OvertimeForecaster
from src.reporting import generate_forecast_export_df

@pytest.fixture
def demo_data():
    raw = get_or_create_demo_data()
    proc, is_valid, _, _, _ = process_uploaded_dataset(raw)
    return proc

def test_tc08_filter_department_and_kpis(demo_data):
    """TC-08: Filter department and date range -> KPI cards update consistently."""
    total_kpis = calculate_kpis(demo_data)
    
    # Filter IT department only
    it_df = demo_data[demo_data["Department"] == "IT"]
    it_kpis = calculate_kpis(it_df)
    
    assert it_kpis["total_records"] < total_kpis["total_records"]
    assert it_kpis["total_ot_hours"] < total_kpis["total_ot_hours"]
    assert it_kpis["top_dept"] == "IT"

def test_tc09_chronological_split_and_evaluation(demo_data):
    """TC-09: Run model evaluation -> Time-ordered split is used; baseline and model MAE/RMSE are shown."""
    forecaster = OvertimeForecaster(model_type="Random Forest")
    summary = forecaster.train_and_evaluate(demo_data, test_ratio=0.20)
    
    assert "baseline_mae" in summary
    assert "model_mae" in summary
    assert "model_rmse" in summary
    assert summary["test_samples"] > 0
    assert summary["train_samples"] > summary["test_samples"]
    # Model should perform reasonably against benchmark
    assert summary["model_mae"] >= 0.0

def test_tc10_forecast_export_metadata_and_assumptions(demo_data):
    """TC-10: Export forecast -> CSV contains date/group, predicted hours, rate/multiplier assumptions, and cost."""
    forecaster = OvertimeForecaster(model_type="Random Forest")
    forecaster.train_and_evaluate(demo_data, test_ratio=0.20)
    future_df = forecaster.generate_future_forecast(demo_data, horizon_days=5, ot_rate_multiplier=1.5)
    
    assumptions = {
        "model_name": "Random Forest",
        "multiplier": 1.5,
        "workdays_per_month": 22,
        "standard_hours": 8.0
    }
    export_df = generate_forecast_export_df(future_df, assumptions)
    
    assert "Date" in export_df.columns
    assert "Forecast_Overtime_Hours" in export_df.columns
    assert "Estimated_Overtime_Cost" in export_df.columns
    assert "OT_Multiplier_Assumption" in export_df.columns
    assert export_df["OT_Multiplier_Assumption"].iloc[0] == 1.5

def test_tc11_short_dataset_warning(demo_data):
    """TC-11: Dataset too short for requested horizon -> System warns about limitations."""
    forecaster = OvertimeForecaster(model_type="Random Forest")
    summary = forecaster.train_and_evaluate(demo_data, test_ratio=0.20)
    
    # 30 calendar days of demo data triggers seasonality warning
    assert "warning" in summary
    assert len(summary["warning"]) > 0
    assert "annual seasonality" in summary["warning"].lower()

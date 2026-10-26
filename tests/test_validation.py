"""
Unit Tests for Data Validation & Quality Checks
Covers TC-01, TC-02, TC-03, TC-07, TC-12 per SRS Section 10.1.
"""
import pytest
import pandas as pd
from src.validation import validate_schema, check_data_quality, sanitize_dataframe, normalize_column_names
from src.data_loader import get_or_create_demo_data, process_uploaded_dataset

def test_tc01_load_provided_sample_csv():
    """TC-01: Load provided sample CSV -> 3,000 rows and 15 columns are detected."""
    demo_df = get_or_create_demo_data()
    assert len(demo_df) == 3000, f"Expected 3000 rows, got {len(demo_df)}"
    assert len(demo_df.columns) >= 15, f"Expected at least 15 columns, got {len(demo_df.columns)}"
    
    # Process through pipeline
    processed_df, is_valid, errors, warnings, diag = process_uploaded_dataset(demo_df)
    assert is_valid is True
    assert len(errors) == 0

def test_tc02_missing_required_columns():
    """TC-02: Upload file missing Employee_ID or Date -> Rejected with clear list."""
    bad_df = pd.DataFrame({
        "Department": ["IT", "HR"],
        "Working_Hours": [8.0, 9.0],
        "Shift": ["Morning", "Evening"],
        "Attendance": [1, 1]
    })
    is_valid, errors, warnings = validate_schema(bad_df)
    assert is_valid is False
    assert any("Employee_ID" in err for err in errors)
    assert any("Date" in err for err in errors)

def test_tc03_invalid_date_values():
    """TC-03: Date has invalid values -> Invalid rows identified; system does not silently invent dates."""
    df_invalid_dates = pd.DataFrame({
        "Employee_ID": ["EMP-001", "EMP-002"],
        "Date": ["2026-09-01", "INVALID_NOT_A_DATE"],
        "Department": ["IT", "HR"],
        "Shift": ["Morning", "Evening"],
        "Attendance": [1, 1],
        "Working_Hours": [8.0, 8.0]
    })
    diag = check_data_quality(df_invalid_dates)
    assert diag["invalid_date_count"] == 1
    assert any("invalid or unparseable dates" in w for w in diag["warnings"])

def test_tc07_attendance_zero_with_working_hours():
    """TC-07: Attendance = 0 with 5 working hours -> Data quality warning appears."""
    df_anomaly = pd.DataFrame({
        "Employee_ID": ["EMP-001"],
        "Date": ["2026-09-01"],
        "Department": ["IT"],
        "Shift": ["Morning"],
        "Attendance": [0],
        "Working_Hours": [5.0]
    })
    diag = check_data_quality(df_anomaly)
    assert diag["attendance_conflict_count"] == 1
    assert any("Absent have working hours > 0" in w for w in diag["warnings"])

def test_tc12_empty_dataset_error_recovery():
    """TC-12: Empty dataset / all rows invalid -> Readable error and recovery path are shown."""
    empty_df = pd.DataFrame()
    is_valid, errors, warnings = validate_schema(empty_df)
    assert is_valid is False
    assert any("empty" in err.lower() for err in errors)

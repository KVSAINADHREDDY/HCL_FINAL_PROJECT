"""
Data Validation and Quality Diagnostics Engine
Enforces schema requirements and data integrity per SRS Sections 3, 4, and 10.
"""
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np

# Strict required columns as defined in SRS Table 4.1
MANDATORY_COLUMNS = [
    "Employee_ID",
    "Date",
    "Department",
    "Shift",
    "Attendance",
    "Working_Hours"
]

# Alias mappings to make system robust to common CSV variations
COLUMN_ALIASES = {
    "emp_id": "Employee_ID",
    "employeeid": "Employee_ID",
    "work_date": "Date",
    "dept": "Department",
    "attendance_status": "Attendance",
    "base_salary": "Monthly_Salary",
    "salary": "Monthly_Salary",
    "experience_years": "Experience",
    "ot_hours": "Overtime_Hours",
    "ot_cost": "Overtime_Cost",
    "hourly_wage": "Hourly_Rate"
}

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column names using case-insensitive mapping and aliases."""
    rename_dict = {}
    for col in df.columns:
        clean = col.strip()
        lower = clean.lower()
        if lower in COLUMN_ALIASES:
            rename_dict[col] = COLUMN_ALIASES[lower]
        elif clean != col:
            rename_dict[col] = clean
    return df.rename(columns=rename_dict)

def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validates presence of required columns and reports missing columns and warnings.
    Returns:
        (is_valid, error_messages, warning_messages)
    """
    errors = []
    warnings = []

    if df is None or df.empty:
        errors.append("The uploaded file is empty. Please provide a CSV file containing employee work records.")
        return False, errors, warnings

    cols = list(df.columns)
    missing_mandatory = [c for c in MANDATORY_COLUMNS if c not in cols]
    
    # Check if either Attendance or Attendance_Status is available
    if "Attendance" in missing_mandatory and "Attendance_Status" in cols:
        missing_mandatory.remove("Attendance")
    
    if missing_mandatory:
        errors.append(f"Missing required columns: {', '.join(missing_mandatory)}. Please inspect your CSV headers.")

    # Check for compensation field (Monthly_Salary or Hourly_Rate or Base_Salary)
    salary_fields = [f for f in ["Monthly_Salary", "Hourly_Rate", "Base_Salary"] if f in cols]
    if not salary_fields:
        warnings.append("Neither 'Monthly_Salary' nor 'Hourly_Rate' was found. Prototype default rate (₹250/hr) will be used for cost estimations.")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings

def check_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs data quality diagnostics:
    - Missing values count per column
    - Date format errors
    - Attendance vs Working Hours logical contradictions
    - Out-of-range working hours (outside 0..24h)
    - Duplicate (Employee_ID, Date) pairs
    """
    diagnostics = {
        "total_records": len(df),
        "total_columns": len(df.columns),
        "missing_values": {},
        "invalid_date_count": 0,
        "duplicate_count": 0,
        "out_of_range_hours_count": 0,
        "attendance_conflict_count": 0,
        "warnings": [],
        "passed_checks": True
    }

    # 1. Missing values
    missing = df.isnull().sum()
    diagnostics["missing_values"] = {k: int(v) for k, v in missing.items() if v > 0}

    # 2. Duplicate records check
    if "Employee_ID" in df.columns and "Date" in df.columns:
        dups = df.duplicated(subset=["Employee_ID", "Date"]).sum()
        diagnostics["duplicate_count"] = int(dups)
        if dups > 0:
            diagnostics["warnings"].append(f"Found {dups} duplicate employee-date records.")

    # 3. Invalid date validation (without silent dropping or fake dates)
    if "Date" in df.columns:
        parsed_dates = pd.to_datetime(df["Date"], errors="coerce")
        invalid_dates = parsed_dates.isnull().sum()
        diagnostics["invalid_date_count"] = int(invalid_dates)
        if invalid_dates > 0:
            diagnostics["warnings"].append(f"Found {invalid_dates} invalid or unparseable dates.")

    # 4. Working hours range check (0 <= Working_Hours <= 24)
    if "Working_Hours" in df.columns:
        numeric_hours = pd.to_numeric(df["Working_Hours"], errors="coerce")
        out_of_range = ((numeric_hours < 0) | (numeric_hours > 24) | numeric_hours.isnull()).sum()
        diagnostics["out_of_range_hours_count"] = int(out_of_range)
        if out_of_range > 0:
            diagnostics["warnings"].append(f"Found {out_of_range} records with out-of-range working hours (< 0 or > 24).")

    # 5. Attendance conflict check (Attendance == 0 but Working_Hours > 0)
    att_col = "Attendance" if "Attendance" in df.columns else ("Attendance_Status" if "Attendance_Status" in df.columns else None)
    if att_col and "Working_Hours" in df.columns:
        if att_col == "Attendance":
            absent_mask = df[att_col] == 0
        else:
            absent_mask = df[att_col].astype(str).str.lower().isin(["0", "absent", "false"])
        
        hours = pd.to_numeric(df["Working_Hours"], errors="coerce").fillna(0)
        conflicts = (absent_mask & (hours > 0)).sum()
        diagnostics["attendance_conflict_count"] = int(conflicts)
        if conflicts > 0:
            diagnostics["warnings"].append(
                f"Data Quality Flag: {conflicts} records marked as Absent have working hours > 0 (TC-07 check)."
            )

    if diagnostics["duplicate_count"] > 0 or diagnostics["invalid_date_count"] > 0 or diagnostics["attendance_conflict_count"] > 0:
        diagnostics["passed_checks"] = False

    return diagnostics

def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans up data types:
    - Normalizes Attendance to 0/1 integer
    - Converts Date to YYYY-MM-DD string and datetime
    - Coerces numerical fields
    """
    df = df.copy()
    
    # Standardize attendance
    if "Attendance_Status" in df.columns and "Attendance" not in df.columns:
        df["Attendance"] = df["Attendance_Status"].apply(
            lambda x: 1 if str(x).strip().lower() in ["1", "present", "true", "yes"] else 0
        )
    elif "Attendance" in df.columns:
        df["Attendance"] = pd.to_numeric(df["Attendance"], errors="coerce").fillna(0).astype(int)

    # Convert Date
    if "Date" in df.columns:
        df["Date_Parsed"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Date"] = df["Date_Parsed"].dt.strftime("%Y-%m-%d")

    # Coerce numerical fields
    numeric_fields = ["Working_Hours", "Overtime_Hours", "Hourly_Rate", "Monthly_Salary", "Base_Salary", "Experience", "Projects_Assigned"]
    for col in numeric_fields:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Standardize Employee_ID as categorical string
    if "Employee_ID" in df.columns:
        df["Employee_ID"] = df["Employee_ID"].astype(str)

    return df

"""
Data Ingestion and Demo Dataset Loader
Handles file upload parsing, fallback sample dataset generation, and pipeline caching.
"""
import os
from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.validation import normalize_column_names, validate_schema, check_data_quality, sanitize_dataframe
from src.cost_calculator import enrich_dataset_calculations

DEMO_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "employee_overtime_cost_forecasting_dataset.csv")

def generate_synthetic_demo_data(
    num_employees: int = 100,
    num_days: int = 30,
    start_date: str = "2026-09-01"
) -> pd.DataFrame:
    """
    Generates the exact baseline synthetic dataset defined in SRS Section 4:
    3,000 records, 100 employee IDs, 30 calendar days, 15 columns.
    """
    np.random.seed(42)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    departments = ["IT", "HR", "Finance", "Production", "Sales"]
    dept_roles = {
        "IT": ["Software Engineer", "DevOps Specialist", "System Admin", "Data Analyst"],
        "HR": ["HR Specialist", "Recruiter", "HR Generalist"],
        "Finance": ["Financial Analyst", "Accountant", "Payroll Specialist"],
        "Production": ["Production Associate", "Quality Inspector", "Machine Operator", "Shift Supervisor"],
        "Sales": ["Sales Executive", "Account Manager", "Business Dev Rep"]
    }
    shifts = ["Morning", "Evening", "Night"]

    employees = []
    for i in range(1, num_employees + 1):
        emp_id = f"EMP-{i:03d}"
        dept = str(np.random.choice(departments, p=[0.25, 0.15, 0.15, 0.30, 0.15]))
        role = str(np.random.choice(dept_roles[dept]))
        exp = int(np.random.randint(1, 18))
        base_sal = 32000 + (exp * 3100) + (14000 if dept in ["IT", "Finance"] else 4000) + int(np.random.randint(-1500, 2500))
        base_sal = round(base_sal, -2)
        hourly_rate = round(base_sal / (22 * 8), 2)
        shift_pref = str(np.random.choice(shifts, p=[0.5, 0.3, 0.2]))
        
        employees.append({
            "Employee_ID": emp_id,
            "Department": dept,
            "Employee_Role": role,
            "Experience": exp,
            "Monthly_Salary": float(base_sal),
            "Hourly_Rate": hourly_rate,
            "Shift": shift_pref
        })

    records = []
    for day_idx in range(num_days):
        cur_date = start_dt + timedelta(days=day_idx)
        date_str = cur_date.strftime("%Y-%m-%d")
        is_weekend = 1 if cur_date.weekday() >= 5 else 0
        is_sunday = 1 if cur_date.weekday() == 6 else 0
        holiday = is_sunday

        for emp in employees:
            att_prob = 0.22 if is_weekend else 0.94
            attendance = 1 if np.random.rand() < att_prob else 0
            projects = int(np.random.randint(1, 6)) if attendance else 0
            weekend_worked = 1 if (is_weekend and attendance == 1) else 0

            if attendance == 1:
                # Higher overtime likelihood in Production & IT
                ot_prob = 0.62 if (emp["Department"] in ["Production", "IT"] or projects >= 4) else 0.32
                if np.random.rand() < ot_prob:
                    ot_hours = float(np.random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]))
                    working_hours = round(8.0 + ot_hours, 2)
                else:
                    ot_hours = 0.0
                    working_hours = 8.0
            else:
                working_hours = 0.0
                ot_hours = 0.0

            ot_cost = round(ot_hours * emp["Hourly_Rate"] * 1.5, 2)

            records.append({
                "Employee_ID": emp["Employee_ID"],
                "Date": date_str,
                "Department": emp["Department"],
                "Employee_Role": emp["Employee_Role"],
                "Experience": emp["Experience"],
                "Shift": emp["Shift"],
                "Attendance": attendance,
                "Holiday": holiday,
                "Weekend_Worked": weekend_worked,
                "Projects_Assigned": projects,
                "Monthly_Salary": emp["Monthly_Salary"],
                "Hourly_Rate": emp["Hourly_Rate"],
                "Working_Hours": working_hours,
                "Overtime_Hours": ot_hours,
                "Overtime_Cost": ot_cost
            })

    df = pd.DataFrame(records)
    return df

def get_or_create_demo_data() -> pd.DataFrame:
    """Loads demo CSV from disk or generates and saves it if absent."""
    os.makedirs(os.path.dirname(DEMO_FILE_PATH), exist_ok=True)
    if os.path.exists(DEMO_FILE_PATH):
        try:
            df = pd.read_csv(DEMO_FILE_PATH)
            if len(df) == 3000 and len(df.columns) >= 15:
                return df
        except Exception:
            pass

    df = generate_synthetic_demo_data(num_employees=100, num_days=30)
    df.to_csv(DEMO_FILE_PATH, index=False)
    return df

def process_uploaded_dataset(
    uploaded_file_or_path,
    workdays_per_month: int = 22,
    standard_hours: float = 8.0,
    multiplier: float = 1.5
) -> Tuple[Optional[pd.DataFrame], bool, List[str], List[str], Dict[str, Any]]:
    """
    Comprehensive pipeline to load, validate, sanitize, and enrich a dataset.
    Returns:
        (processed_df, is_valid, error_list, warning_list, diagnostics_dict)
    """
    try:
        if isinstance(uploaded_file_or_path, pd.DataFrame):
            df_raw = uploaded_file_or_path.copy()
        elif isinstance(uploaded_file_or_path, str):
            df_raw = pd.read_csv(uploaded_file_or_path)
        else:
            df_raw = pd.read_csv(uploaded_file_or_path)
    except Exception as e:
        return None, False, [f"Failed to parse CSV file: {str(e)}"], [], {}

    # Step 1: Normalize column names
    df_norm = normalize_column_names(df_raw)

    # Step 2: Validate schema
    is_valid, errors, warnings = validate_schema(df_norm)
    if not is_valid:
        return df_norm, False, errors, warnings, {}

    # Step 3: Sanitize data types
    df_sanitized = sanitize_dataframe(df_norm)

    # Step 4: Quality diagnostics
    diagnostics = check_data_quality(df_sanitized)

    # Step 5: Cost enrichment & checks
    df_enriched, cost_diag = enrich_dataset_calculations(
        df_sanitized,
        workdays_per_month=workdays_per_month,
        standard_hours=standard_hours,
        default_multiplier=multiplier
    )
    diagnostics.update(cost_diag)

    return df_enriched, True, errors, warnings, diagnostics

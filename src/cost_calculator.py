"""
Cost and Overtime Calculation Engine
Implements business rules and formulas defined in SRS Section 5.
"""
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

DEFAULT_WORKDAYS_PER_MONTH = 22
DEFAULT_HOURS_PER_DAY = 8.0
DEFAULT_OT_MULTIPLIER = 1.5
DEFAULT_WEEKEND_OT_MULTIPLIER = 2.0

def calculate_hourly_rate(
    monthly_salary: float,
    workdays_per_month: int = DEFAULT_WORKDAYS_PER_MONTH,
    hours_per_day: float = DEFAULT_HOURS_PER_DAY
) -> float:
    """
    Computes effective base hourly rate from monthly salary.
    Formula: Hourly_Rate = Monthly_Salary / (Standard_Workdays_Per_Month * Standard_Hours_Per_Day)
    """
    total_hours = workdays_per_month * hours_per_day
    if total_hours <= 0:
        raise ValueError("Total monthly standard hours must be positive.")
    if monthly_salary < 0:
        raise ValueError("Monthly salary cannot be negative.")
    return round(monthly_salary / total_hours, 2)

def calculate_overtime_hours(
    working_hours: float,
    scheduled_hours: float = DEFAULT_HOURS_PER_DAY,
    attendance: Optional[int] = 1
) -> float:
    """
    Computes daily overtime hours.
    Overtime_Hours = max(0.0, Working_Hours - Scheduled_Hours)
    If employee is absent (attendance == 0), overtime is 0.0.
    """
    if attendance == 0:
        return 0.0
    if working_hours < 0:
        raise ValueError("Working hours cannot be negative.")
    return max(0.0, round(working_hours - scheduled_hours, 2))

def calculate_overtime_cost(
    overtime_hours: float,
    hourly_rate: float,
    multiplier: float = DEFAULT_OT_MULTIPLIER
) -> float:
    """
    Computes estimated overtime cost.
    Formula: Overtime_Cost = Overtime_Hours * Hourly_Rate * Overtime_Multiplier
    """
    if overtime_hours < 0 or hourly_rate < 0 or multiplier < 0:
        raise ValueError("Inputs to overtime cost must be non-negative.")
    return round(overtime_hours * hourly_rate * multiplier, 2)

def enrich_dataset_calculations(
    df: pd.DataFrame,
    workdays_per_month: int = DEFAULT_WORKDAYS_PER_MONTH,
    standard_hours: float = DEFAULT_HOURS_PER_DAY,
    default_multiplier: float = DEFAULT_OT_MULTIPLIER,
    weekend_multiplier: float = DEFAULT_WEEKEND_OT_MULTIPLIER
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates and enriches dataframe with standard hourly rate, overtime hours, and overtime costs.
    Identifies any discrepancies between original and recalculated costs.
    """
    df = df.copy()
    diagnostics = {
        "cost_discrepancies_count": 0,
        "max_discrepancy": 0.0,
        "records_recalculated": len(df)
    }

    # 1. Standardize or compute Hourly_Rate
    if "Hourly_Rate" not in df.columns or df["Hourly_Rate"].isnull().any():
        if "Monthly_Salary" in df.columns:
            divisor = workdays_per_month * standard_hours
            df["Hourly_Rate"] = (df["Monthly_Salary"] / divisor).round(2)
        elif "Base_Salary" in df.columns:
            divisor = workdays_per_month * standard_hours
            df["Hourly_Rate"] = (df["Base_Salary"] / divisor).round(2)
        else:
            df["Hourly_Rate"] = 250.0  # Safe fallback default in INR

    # 2. Reconcile Overtime_Hours
    if "Scheduled_Hours" in df.columns:
        scheduled = df["Scheduled_Hours"]
    else:
        scheduled = standard_hours

    # Enforce attendance = 0 => Working_Hours = 0 and Overtime_Hours = 0
    if "Attendance" in df.columns:
        present_mask = df["Attendance"] == 1
    elif "Attendance_Status" in df.columns:
        present_mask = df["Attendance_Status"].astype(str).str.lower().isin(["1", "present"])
    else:
        present_mask = pd.Series(True, index=df.index)

    computed_ot_hours = np.where(
        present_mask,
        np.maximum(0.0, df["Working_Hours"] - scheduled),
        0.0
    ).round(2)

    if "Overtime_Hours" not in df.columns or df["Overtime_Hours"].isnull().all():
        df["Overtime_Hours"] = computed_ot_hours

    # 3. Determine Overtime Multiplier
    if "Overtime_Multiplier" in df.columns and not df["Overtime_Multiplier"].isnull().all():
        multipliers = df["Overtime_Multiplier"]
    else:
        # Check weekend/holiday
        is_weekend = df.get("Weekend_Worked", pd.Series(0, index=df.index)) == 1
        is_holiday = df.get("Holiday", pd.Series(0, index=df.index)) == 1
        multipliers = np.where(is_weekend | is_holiday, weekend_multiplier, default_multiplier)
        df["Overtime_Multiplier"] = multipliers

    # 4. Compute Expected Overtime Cost
    expected_cost = (df["Overtime_Hours"] * df["Hourly_Rate"] * df["Overtime_Multiplier"]).round(2)
    
    if "Overtime_Cost" in df.columns and not df["Overtime_Cost"].isnull().all():
        diff = (df["Overtime_Cost"] - expected_cost).abs()
        discrepancies = diff > 1.0  # tolerance threshold of 1 INR
        diagnostics["cost_discrepancies_count"] = int(discrepancies.sum())
        diagnostics["max_discrepancy"] = float(diff.max()) if len(diff) > 0 else 0.0
        df["Calculated_Overtime_Cost"] = expected_cost
    else:
        df["Overtime_Cost"] = expected_cost
        df["Calculated_Overtime_Cost"] = expected_cost

    return df, diagnostics

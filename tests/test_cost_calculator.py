"""
Unit Tests for Cost and Overtime Calculation Engine
Covers TC-04, TC-05, TC-06 per SRS Section 10.1.
"""
import pytest
from src.cost_calculator import (
    calculate_hourly_rate,
    calculate_overtime_hours,
    calculate_overtime_cost,
    enrich_dataset_calculations
)
import pandas as pd

def test_tc04_decimal_hours_interpretation():
    """TC-04: Working_Hours = 8.5 -> System interprets this as 8 hours 30 minutes."""
    working_hours = 8.5
    scheduled_hours = 8.0
    ot = calculate_overtime_hours(working_hours, scheduled_hours=scheduled_hours)
    assert ot == 0.5  # 0.5 hours = 30 minutes

def test_tc05_overtime_hours_derivation():
    """TC-05: Working_Hours = 10, scheduled hours = 8 -> Derived overtime is 2 hours."""
    ot = calculate_overtime_hours(working_hours=10.0, scheduled_hours=8.0)
    assert ot == 2.0

def test_tc06_overtime_cost_calculation():
    """TC-06: OT = 2, hourly rate = 300, multiplier = 1.5 -> Estimated overtime cost is 900."""
    cost = calculate_overtime_cost(overtime_hours=2.0, hourly_rate=300.0, multiplier=1.5)
    assert cost == 900.0

def test_hourly_rate_derivation_from_monthly_salary():
    """Verifies Appendix A.1 worked example: 60,000 / (22 * 8) = 340.91."""
    rate = calculate_hourly_rate(monthly_salary=60000.0, workdays_per_month=22, hours_per_day=8.0)
    assert rate == 340.91

    # Overtime cost for 3 hours at 1.5 multiplier
    cost = calculate_overtime_cost(overtime_hours=3.0, hourly_rate=rate, multiplier=1.5)
    assert cost == 1534.10  # 3 * 340.91 * 1.5 = 1534.095 -> 1534.10

def test_attendance_zero_forces_zero_overtime():
    """When attendance is 0, overtime hours must be 0."""
    ot = calculate_overtime_hours(working_hours=9.0, scheduled_hours=8.0, attendance=0)
    assert ot == 0.0

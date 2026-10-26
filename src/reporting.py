"""
Reporting and Data Export Engine
Generates standardized CSV downloads and executive summaries per SRS FR-14.
"""
from typing import Dict, Any, Optional
import pandas as pd
import io

def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Converts a DataFrame into UTF-8 encoded CSV bytes for Streamlit download button."""
    return df.to_csv(index=False).encode("utf-8")

def generate_forecast_export_df(forecast_df: pd.DataFrame, assumptions: Dict[str, Any]) -> pd.DataFrame:
    """
    Formats the forecast output table with transparent metadata columns
    (Assumptions, Forecast Horizon, Multipliers) per SRS TC-10.
    """
    export_df = forecast_df.copy()
    export_df["Forecast_Status"] = "ESTIMATED_VALUE"
    export_df["Model_Used"] = assumptions.get("model_name", "Random Forest")
    export_df["OT_Multiplier_Assumption"] = assumptions.get("multiplier", 1.5)
    export_df["Workdays_Per_Month_Assumption"] = assumptions.get("workdays_per_month", 22)
    export_df["Standard_Daily_Hours_Assumption"] = assumptions.get("standard_hours", 8.0)
    return export_df

def generate_executive_summary_markdown(kpis: Dict[str, Any], model_metrics: Optional[Dict[str, Any]] = None) -> str:
    """Generates a structured markdown report summarizing findings and model performance."""
    summary = f"""# Executive Overtime & Workforce Cost Summary

## Key Historical Performance Indicators
- **Total Historical Overtime Recorded:** {kpis.get('total_ot_hours', 0):,.1f} decimal hours
- **Total Estimated Overtime Cost:** ₹{kpis.get('total_ot_cost', 0):,.2f}
- **Workforce Attendance Rate:** {kpis.get('attendance_rate', 0)}%
- **Average Overtime per Present Employee Record:** {kpis.get('avg_ot_per_present', 0)} hours
- **Highest Overtime-Prone Department:** {kpis.get('top_dept', 'N/A')} ({kpis.get('top_dept_hours', 0)} hours)
- **Active Tracked Employees:** {kpis.get('active_employees', 0)}
"""
    if model_metrics:
        summary += f"""
## Machine Learning Model Evaluation
- **Evaluation Method:** Strict Chronological Time Split (No Future Data Leakage)
- **Baseline Model MAE:** {model_metrics.get('baseline_mae', 'N/A')} hrs
- **Trained Model MAE:** {model_metrics.get('model_mae', 'N/A')} hrs
- **Error Improvement:** {model_metrics.get('mae_improvement_pct', 0)}% over baseline
- **RMSE:** {model_metrics.get('model_rmse', 'N/A')} hrs
"""
    summary += """
## Governance & Limitations Notice
- Predictions are mathematical estimations based on past workload, department trends, and attendance patterns.
- Synthetic prototype data demonstrates pipeline capabilities and does not represent real enterprise payroll.
"""
    return summary

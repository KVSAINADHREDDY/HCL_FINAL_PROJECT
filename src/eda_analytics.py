"""
Exploratory Data Analysis (EDA) and Visualization Engine
Calculates executive KPIs and builds modern, interactive Plotly visualizations.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Professional Color Palette
CHART_THEME = {
    "primary": "#2563EB",
    "secondary": "#06B6D4",
    "accent": "#F59E0B",
    "success": "#10B981",
    "danger": "#EF4444",
    "dark": "#0F172A",
    "grid": "#E2E8F0",
    "background": "rgba(255, 255, 255, 0)",
    "font_family": "Plus Jakarta Sans, Inter, sans-serif"
}

def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes key performance indicators defined in SRS FR-05:
    - Total overtime hours
    - Total estimated overtime cost
    - Attendance rate (%)
    - Average overtime hours per present record
    - Overtime-prone departments
    """
    if df.empty:
        return {
            "total_ot_hours": 0.0,
            "total_ot_cost": 0.0,
            "attendance_rate": 0.0,
            "avg_ot_per_present": 0.0,
            "top_dept": "N/A",
            "top_dept_hours": 0.0,
            "active_employees": 0,
            "total_records": 0
        }

    total_records = len(df)
    active_employees = df["Employee_ID"].nunique() if "Employee_ID" in df.columns else 0

    # Overtime hours & cost
    total_ot_hours = round(float(df["Overtime_Hours"].sum()), 2) if "Overtime_Hours" in df.columns else 0.0
    
    cost_col = "Calculated_Overtime_Cost" if "Calculated_Overtime_Cost" in df.columns else "Overtime_Cost"
    total_ot_cost = round(float(df[cost_col].sum()), 2) if cost_col in df.columns else 0.0

    # Attendance Rate
    if "Attendance" in df.columns:
        present_count = int((df["Attendance"] == 1).sum())
        attendance_rate = round((present_count / total_records) * 100, 1)
    else:
        present_count = total_records
        attendance_rate = 100.0

    # Average OT per present record
    avg_ot_per_present = round(total_ot_hours / max(1, present_count), 2)

    # Overtime-prone departments
    if "Department" in df.columns and "Overtime_Hours" in df.columns:
        dept_grp = df.groupby("Department")["Overtime_Hours"].sum()
        if not dept_grp.empty:
            top_dept = str(dept_grp.idxmax())
            top_dept_hours = round(float(dept_grp.max()), 1)
        else:
            top_dept, top_dept_hours = "N/A", 0.0
    else:
        top_dept, top_dept_hours = "N/A", 0.0

    return {
        "total_ot_hours": total_ot_hours,
        "total_ot_cost": total_ot_cost,
        "attendance_rate": attendance_rate,
        "avg_ot_per_present": avg_ot_per_present,
        "top_dept": top_dept,
        "top_dept_hours": top_dept_hours,
        "active_employees": active_employees,
        "total_records": total_records
    }

def create_overtime_trend_chart(df: pd.DataFrame) -> go.Figure:
    """
    Plots daily overtime hours and estimated overtime costs as a dual-axis interactive time series.
    """
    if "Date" not in df.columns or "Overtime_Hours" not in df.columns:
        return go.Figure()

    cost_col = "Calculated_Overtime_Cost" if "Calculated_Overtime_Cost" in df.columns else "Overtime_Cost"

    daily = df.groupby("Date").agg({
        "Overtime_Hours": "sum",
        cost_col: "sum"
    }).reset_index().sort_values("Date")

    fig = go.Figure()

    # Overtime Hours Area/Line
    fig.add_trace(go.Scatter(
        x=daily["Date"],
        y=daily["Overtime_Hours"],
        name="Overtime Hours",
        mode="lines+markers",
        line=dict(color=CHART_THEME["primary"], width=3),
        fill="tozeroy",
        fillcolor="rgba(37, 99, 235, 0.08)",
        marker=dict(size=6, color=CHART_THEME["primary"]),
        hovertemplate="<b>Date:</b> %{x}<br><b>OT Hours:</b> %{y:.1f} hrs<extra></extra>"
    ))

    # Overtime Cost Line on Secondary Y-Axis
    fig.add_trace(go.Scatter(
        x=daily["Date"],
        y=daily[cost_col],
        name="Overtime Cost (₹)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color=CHART_THEME["accent"], width=2.5, dash="dot"),
        marker=dict(size=5, color=CHART_THEME["accent"]),
        hovertemplate="<b>Date:</b> %{x}<br><b>Cost:</b> ₹%{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="<b>Daily Overtime Hours & Financial Cost Trend</b>", font=dict(size=16)),
        xaxis=dict(title="Work Date", showgrid=True, gridcolor=CHART_THEME["grid"]),
        yaxis=dict(
            title=dict(text="Total Overtime Hours", font=dict(color=CHART_THEME["primary"])),
            tickfont=dict(color=CHART_THEME["primary"]),
            showgrid=True,
            gridcolor=CHART_THEME["grid"]
        ),
        yaxis2=dict(
            title=dict(text="Total Cost (INR ₹)", font=dict(color=CHART_THEME["accent"])),
            tickfont=dict(color=CHART_THEME["accent"]),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        paper_bgcolor=CHART_THEME["background"],
        plot_bgcolor=CHART_THEME["background"],
        margin=dict(l=40, r=40, t=50, b=40),
        font=dict(family=CHART_THEME["font_family"])
    )
    return fig

def create_department_breakdown_chart(df: pd.DataFrame) -> go.Figure:
    """
    Renders bar chart comparing Overtime Hours across Departments with Cost tooltips.
    """
    if "Department" not in df.columns or "Overtime_Hours" not in df.columns:
        return go.Figure()

    cost_col = "Calculated_Overtime_Cost" if "Calculated_Overtime_Cost" in df.columns else "Overtime_Cost"
    dept_df = df.groupby("Department").agg({
        "Overtime_Hours": "sum",
        cost_col: "sum",
        "Employee_ID": "nunique"
    }).reset_index().sort_values("Overtime_Hours", ascending=False)

    fig = px.bar(
        dept_df,
        x="Department",
        y="Overtime_Hours",
        color="Overtime_Hours",
        color_continuous_scale="Blues",
        text_auto=".1f",
        title="<b>Overtime Hours Distribution by Department</b>"
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Total OT: %{y:.1f} hrs<br>Estimated Cost: ₹%{customdata[0]:,.2f}<extra></extra>",
        customdata=dept_df[[cost_col]]
    )

    fig.update_layout(
        xaxis=dict(title="Department", showgrid=False),
        yaxis=dict(title="Total Overtime Hours", showgrid=True, gridcolor=CHART_THEME["grid"]),
        coloraxis_showscale=False,
        paper_bgcolor=CHART_THEME["background"],
        plot_bgcolor=CHART_THEME["background"],
        font=dict(family=CHART_THEME["font_family"]),
        margin=dict(l=30, r=30, t=50, b=30)
    )
    return fig

def create_shift_donut_chart(df: pd.DataFrame) -> go.Figure:
    """
    Renders donut chart showing overtime hours share by Shift (Morning, Evening, Night).
    """
    if "Shift" not in df.columns or "Overtime_Hours" not in df.columns:
        return go.Figure()

    shift_df = df.groupby("Shift")["Overtime_Hours"].sum().reset_index()

    colors = [CHART_THEME["primary"], CHART_THEME["secondary"], CHART_THEME["accent"]]

    fig = go.Figure(data=[go.Pie(
        labels=shift_df["Shift"],
        values=shift_df["Overtime_Hours"],
        hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hovertemplate="<b>Shift:</b> %{label}<br><b>OT Hours:</b> %{value:.1f} hrs (%{percent})<extra></extra>"
    )])

    fig.update_layout(
        title=dict(text="<b>Overtime Share by Work Shift</b>", font=dict(size=16)),
        paper_bgcolor=CHART_THEME["background"],
        font=dict(family=CHART_THEME["font_family"]),
        showlegend=True,
        margin=dict(l=30, r=30, t=50, b=30)
    )
    return fig

def create_workload_correlation_chart(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot with trendline: Active Projects Assigned vs Overtime Hours.
    """
    if "Projects_Assigned" not in df.columns or "Overtime_Hours" not in df.columns:
        return go.Figure()

    present_df = df[df["Overtime_Hours"] > 0] if (df["Overtime_Hours"] > 0).any() else df

    fig = px.box(
        present_df,
        x="Projects_Assigned",
        y="Overtime_Hours",
        color="Department",
        title="<b>Workload Pressure: Overtime Distribution by Active Projects</b>"
    )

    fig.update_layout(
        xaxis=dict(title="Number of Projects Assigned", dtick=1),
        yaxis=dict(title="Overtime Hours Logged", showgrid=True, gridcolor=CHART_THEME["grid"]),
        paper_bgcolor=CHART_THEME["background"],
        plot_bgcolor=CHART_THEME["background"],
        font=dict(family=CHART_THEME["font_family"]),
        margin=dict(l=30, r=30, t=50, b=30)
    )
    return fig

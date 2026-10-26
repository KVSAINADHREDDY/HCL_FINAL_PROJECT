"""
Employee Overtime Cost Forecasting System
Main Streamlit Application
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Local modules
from src.ui_theme import apply_custom_theme, render_hero_header, render_kpi_card
from src.validation import validate_schema, check_data_quality, MANDATORY_COLUMNS
from src.data_loader import process_uploaded_dataset, get_or_create_demo_data
from src.eda_analytics import (
    calculate_kpis,
    create_overtime_trend_chart,
    create_department_breakdown_chart,
    create_shift_donut_chart,
    create_workload_correlation_chart
)
from src.forecasting import OvertimeForecaster
from src.reporting import dataframe_to_csv_bytes, generate_forecast_export_df, generate_executive_summary_markdown

# Page Configuration
st.set_page_config(
    page_title="Employee Overtime Cost Forecasting System",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Modern CSS & Fonts
apply_custom_theme()

# Session State Initialization
if "raw_df" not in st.session_state:
    st.session_state["raw_df"] = None
if "processed_df" not in st.session_state:
    st.session_state["processed_df"] = None
if "dataset_name" not in st.session_state:
    st.session_state["dataset_name"] = "No dataset loaded"
if "diagnostics" not in st.session_state:
    st.session_state["diagnostics"] = {}
if "forecaster" not in st.session_state:
    st.session_state["forecaster"] = None
if "forecast_results" not in st.session_state:
    st.session_state["forecast_results"] = None
if "future_forecast" not in st.session_state:
    st.session_state["future_forecast"] = None

# Top Hero Header
render_hero_header(
    title="Employee Overtime Cost Forecasting System",
    subtitle="Estimate future overtime hours and costs to support workforce budgeting, prevent budget overruns, and schedule efficiently.",
    status_badge="SRS v1.0 • Enterprise Analytics"
)

# ----------------- SIDEBAR CONFIGURATION & FILTERS -----------------
with st.sidebar:
    st.markdown("### ⚙️ System Configuration")
    st.caption("Configurable business assumptions per SRS Section 5.")
    
    cfg_workdays = st.number_input("Standard Workdays / Month", min_value=15, max_value=31, value=22, step=1)
    cfg_standard_hours = st.number_input("Standard Shift Hours / Day", min_value=4.0, max_value=12.0, value=8.0, step=0.5)
    cfg_ot_multiplier = st.number_input("Overtime Cost Multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)

    st.markdown("---")
    st.markdown("### 📂 Dataset Status")
    if st.session_state["processed_df"] is not None:
        st.success(f"**Loaded:** {st.session_state['dataset_name']}")
        st.markdown(f"- **Rows:** {len(st.session_state['processed_df']):,}")
        st.markdown(f"- **Columns:** {len(st.session_state['processed_df'].columns)}")
    else:
        st.info("No active dataset. Upload a CSV or load demo data in Tab 1.")

    st.markdown("---")
    st.markdown("### 🔍 Global Data Filters")
    
    filter_dept = []
    filter_shift = []
    date_range = None
    
    if st.session_state["processed_df"] is not None:
        df_for_filters = st.session_state["processed_df"]
        
        # Department Filter
        if "Department" in df_for_filters.columns:
            all_depts = sorted(list(df_for_filters["Department"].dropna().unique()))
            filter_dept = st.multiselect("Filter Departments", options=all_depts, default=[])
            
        # Shift Filter
        if "Shift" in df_for_filters.columns:
            all_shifts = sorted(list(df_for_filters["Shift"].dropna().unique()))
            filter_shift = st.multiselect("Filter Shifts", options=all_shifts, default=[])

        # Date Range Filter
        if "Date" in df_for_filters.columns:
            min_date = pd.to_datetime(df_for_filters["Date"]).min().date()
            max_date = pd.to_datetime(df_for_filters["Date"]).max().date()
            date_range = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    st.markdown("---")
    st.caption("Developed per HCL Mini Project Specification • Python & Streamlit")

# Function to apply active sidebar filters
def get_filtered_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    filtered = df.copy()
    if filter_dept:
        filtered = filtered[filtered["Department"].isin(filter_dept)]
    if filter_shift:
        filtered = filtered[filtered["Shift"].isin(filter_shift)]
    if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered["Date_DT"] = pd.to_datetime(filtered["Date"]).dt.date
        filtered = filtered[(filtered["Date_DT"] >= start_d) & (filtered["Date_DT"] <= end_d)]
        filtered = filtered.drop(columns=["Date_DT"])
    return filtered

# ----------------- MAIN TABBED WORKFLOW -----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 1. Data Ingestion",
    "📋 2. Data Explorer",
    "📊 3. Exploratory Data Analysis (EDA)",
    "🤖 4. ML Overtime Forecasting",
    "💡 5. What-If Simulator",
    "📑 6. Export & Reports"
])

# ----------------- TAB 1: DATA INGESTION -----------------
with tab1:
    st.markdown("### 📥 Step 1: Upload Dataset or Load Synthetic Demo Data")
    st.markdown(
        "Upload your employee attendance CSV file with records of working hours, departments, and shifts, "
        "or click **Load Sample Demo Dataset** to test with the verified 3,000-record baseline."
    )

    col_btn1, col_btn2 = st.columns([1.2, 2.8])
    with col_btn1:
        load_demo_clicked = st.button("🚀 Load Sample Demo Dataset (3,000 Rows)", type="primary", use_container_width=True)

    with col_btn2:
        uploaded_file = st.file_uploader("Or Upload CSV File", type=["csv"], label_visibility="collapsed")

    # Ingestion Actions
    if load_demo_clicked:
        with st.spinner("Loading demo dataset with 100 employees and 30 days..."):
            demo_raw = get_or_create_demo_data()
            proc_df, is_valid, errs, warns, diag = process_uploaded_dataset(
                demo_raw,
                workdays_per_month=cfg_workdays,
                standard_hours=cfg_standard_hours,
                multiplier=cfg_ot_multiplier
            )
            st.session_state["raw_df"] = demo_raw
            st.session_state["processed_df"] = proc_df
            st.session_state["dataset_name"] = "Sample Demo Dataset (3,000 records)"
            st.session_state["diagnostics"] = diag
            st.rerun()

    if uploaded_file is not None and (st.session_state.get("last_uploaded_name") != uploaded_file.name):
        with st.spinner("Validating and parsing uploaded dataset..."):
            proc_df, is_valid, errs, warns, diag = process_uploaded_dataset(
                uploaded_file,
                workdays_per_month=cfg_workdays,
                standard_hours=cfg_standard_hours,
                multiplier=cfg_ot_multiplier
            )
            if not is_valid:
                st.error("❌ **Upload Validation Failed:**")
                for err in errs:
                    st.error(f"- {err}")
            else:
                st.session_state["raw_df"] = proc_df
                st.session_state["processed_df"] = proc_df
                st.session_state["dataset_name"] = uploaded_file.name
                st.session_state["diagnostics"] = diag
                st.session_state["last_uploaded_name"] = uploaded_file.name
                st.success("✅ Dataset successfully validated and loaded!")
                st.rerun()

    # Data Quality & Validation Summary Panel
    if st.session_state["processed_df"] is not None:
        df_cur = st.session_state["processed_df"]
        diag = st.session_state["diagnostics"]

        st.markdown("---")
        st.markdown("#### 🩺 Data Health & Validation Diagnostics")

        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        with col_q1:
            st.metric("Total Records", f"{len(df_cur):,}")
        with col_q2:
            dups = diag.get("duplicate_count", 0)
            st.metric("Duplicate Pairs", dups, delta="Clean" if dups == 0 else f"{dups} Duplicates", delta_color="normal" if dups == 0 else "inverse")
        with col_q3:
            conflicts = diag.get("attendance_conflict_count", 0)
            st.metric("Attendance Anomalies", conflicts, delta="None" if conflicts == 0 else "TC-07 Review", delta_color="normal" if conflicts == 0 else "inverse")
        with col_q4:
            discrepancies = diag.get("cost_discrepancies_count", 0)
            st.metric("Cost Discrepancies", discrepancies, delta="Verified" if discrepancies == 0 else f"{discrepancies} Recalculated")

        # Display Schema Pill Badges
        st.markdown("##### Detected Schema Columns")
        cols_html = " ".join([f"<span class='status-pill pill-info'>{col}</span>" for col in df_cur.columns])
        st.markdown(cols_html, unsafe_allow_html=True)

        if diag.get("warnings"):
            with st.expander("⚠️ View Data Quality Advisories & Notes"):
                for w in diag["warnings"]:
                    st.warning(w)

# ----------------- TAB 2: DATA EXPLORER & FULL DATA DISPLAY -----------------
with tab2:
    st.markdown("### 📋 Step 2: Data Exploration & Inspection")
    if st.session_state["processed_df"] is None:
        st.warning("⚠️ No dataset loaded. Please upload a file or click 'Load Demo Data' in Tab 1.")
    else:
        df_active = get_filtered_df(st.session_state["processed_df"])

        # Display Options Header
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.5, 1.5, 1])
        with col_ctrl1:
            display_mode = st.radio(
                "Display Scope:",
                options=["Display All Data", "Display Sliced / Paginated Data"],
                horizontal=True
            )
        with col_ctrl2:
            search_query = st.text_input("🔍 Quick Search (Employee ID, Role, Department):", "")
        with col_ctrl3:
            st.write("")
            st.write("")
            st.download_button(
                label="📥 Export Current View to CSV",
                data=dataframe_to_csv_bytes(df_active),
                file_name="overtime_dataset_view.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Apply search if entered
        if search_query.strip():
            q = search_query.strip().lower()
            str_cols = [c for c in ["Employee_ID", "Department", "Employee_Role", "Shift"] if c in df_active.columns]
            mask = False
            for c in str_cols:
                mask = mask | (df_active[c].astype(str).str.lower().str.contains(q))
            df_active = df_active[mask]

        st.caption(f"Displaying **{len(df_active):,}** matching records out of **{len(st.session_state['processed_df']):,}** total records.")

        # Column Selector
        all_cols = list(df_active.columns)
        selected_cols = st.multiselect(
            "Select Columns to Display:",
            options=all_cols,
            default=all_cols[:12] if len(all_cols) > 12 else all_cols
        )

        # Table Display
        if display_mode == "Display All Data":
            st.dataframe(df_active[selected_cols], use_container_width=True, height=500)
        else:
            col_rows, col_page = st.columns([1, 2])
            with col_rows:
                rows_per_page = st.selectbox("Rows per page:", options=[25, 50, 100, 250], index=1)
            total_pages = max(1, int(np.ceil(len(df_active) / rows_per_page)))
            with col_page:
                page = st.number_input("Page:", min_value=1, max_value=total_pages, value=1, step=1)
            
            start_idx = (page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            st.dataframe(df_active[selected_cols].iloc[start_idx:end_idx], use_container_width=True, height=450)

        # Data Profiling Expander
        with st.expander("📊 View Column Summary Statistics"):
            st.dataframe(df_active.describe().T.round(2), use_container_width=True)

# ----------------- TAB 3: EXPLORATORY DATA ANALYSIS (EDA) & KPIS -----------------
with tab3:
    st.markdown("### 📊 Step 3: Exploratory Analytics & Overtime Intelligence")
    if st.session_state["processed_df"] is None:
        st.warning("⚠️ No dataset loaded. Please upload a file or click 'Load Demo Data' in Tab 1.")
    else:
        df_eda = get_filtered_df(st.session_state["processed_df"])
        kpis = calculate_kpis(df_eda)

        # Executive KPI Cards Grid
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        with kpi_col1:
            render_kpi_card(
                label="Total Overtime",
                value=f"{kpis['total_ot_hours']:,.1f} hrs",
                subtext=f"Avg {kpis['avg_ot_per_present']} hrs / present record",
                trend_type="highlight",
                icon="⏱️"
            )
        with kpi_col2:
            render_kpi_card(
                label="Estimated OT Cost",
                value=f"₹{kpis['total_ot_cost']:,.2f}",
                subtext=f"Multiplier: {cfg_ot_multiplier}x standard",
                trend_type="warning",
                icon="💰"
            )
        with kpi_col3:
            render_kpi_card(
                label="Attendance Rate",
                value=f"{kpis['attendance_rate']}%",
                subtext=f"Across {kpis['active_employees']} tracked staff",
                trend_type="positive",
                icon="👥"
            )
        with kpi_col4:
            render_kpi_card(
                label="Top OT Department",
                value=kpis['top_dept'],
                subtext=f"{kpis['top_dept_hours']} hrs logged",
                trend_type="highlight",
                icon="🏢"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Main Chart Row: Time Series Overtime Trend
        st.plotly_chart(create_overtime_trend_chart(df_eda), use_container_width=True)

        # Secondary Row: Department & Shift Visualizations
        chart_col1, chart_col2 = st.columns([1.4, 1.0])
        with chart_col1:
            st.plotly_chart(create_department_breakdown_chart(df_eda), use_container_width=True)
        with chart_col2:
            st.plotly_chart(create_shift_donut_chart(df_eda), use_container_width=True)

        # Workload Pressure Chart
        st.plotly_chart(create_workload_correlation_chart(df_eda), use_container_width=True)

# ----------------- TAB 4: MACHINE LEARNING FORECASTING -----------------
with tab4:
    st.markdown("### 🤖 Step 4: Leakage-Free Overtime Forecasting & Model Evaluation")
    st.caption(
        "Evaluation strictly follows SRS Section 6: Chronological time-series split (no future data leakage), "
        "transparent MAE & RMSE evaluation against a historical baseline, and feature importance drivers."
    )

    if st.session_state["processed_df"] is None:
        st.warning("⚠️ No dataset loaded. Please upload a file or click 'Load Demo Data' in Tab 1.")
    else:
        df_ml = st.session_state["processed_df"]

        col_m1, col_m2, col_m3 = st.columns([1.5, 1.2, 1.3])
        with col_m1:
            model_choice = st.selectbox(
                "Select Machine Learning Algorithm:",
                options=["Random Forest", "Gradient Boosting"],
                index=0
            )
        with col_m2:
            test_split = st.slider("Chronological Test Split Ratio:", min_value=0.10, max_value=0.35, value=0.20, step=0.05)
        with col_m3:
            st.write("")
            st.write("")
            train_clicked = st.button("🚀 Train & Evaluate Model", type="primary", use_container_width=True)

        if train_clicked or st.session_state["forecast_results"] is None:
            with st.spinner("Training model with chronological time split..."):
                forecaster = OvertimeForecaster(model_type=model_choice)
                summary = forecaster.train_and_evaluate(df_ml, test_ratio=test_split)
                st.session_state["forecaster"] = forecaster
                st.session_state["forecast_results"] = summary

        summary = st.session_state["forecast_results"]

        if summary:
            # Metric Scorecards
            st.markdown("#### 🎯 Model Evaluation Metrics (Test Horizon)")
            score_col1, score_col2, score_col3, score_col4 = st.columns(4)
            with score_col1:
                st.metric("Baseline MAE", f"{summary['baseline_mae']} hrs", help="Benchmark predicting training mean")
            with score_col2:
                st.metric("Trained Model MAE", f"{summary['model_mae']} hrs", delta=f"{summary['mae_improvement_pct']}% error reduction", delta_color="normal")
            with score_col3:
                st.metric("Model RMSE", f"{summary['model_rmse']} hrs")
            with score_col4:
                st.metric("Time Split Cutoff", str(summary['split_date']), help="Training on records before this date; testing on subsequent dates.")

            if summary.get("warning"):
                st.info(f"ℹ️ **Horizon Note:** {summary['warning']}")

            # Visual Actual vs Predicted Chart
            daily_comp = summary["daily_comparison"]
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=daily_comp["Date"],
                y=daily_comp["Actual_Overtime_Hours"],
                name="Actual Overtime",
                mode="lines+markers",
                line=dict(color="#10B981", width=3)
            ))
            fig_comp.add_trace(go.Scatter(
                x=daily_comp["Date"],
                y=daily_comp["Predicted_Overtime_Hours"],
                name=f"Predicted ({model_choice})",
                mode="lines+markers",
                line=dict(color="#2563EB", width=2.5, dash="dash")
            ))
            fig_comp.add_trace(go.Scatter(
                x=daily_comp["Date"],
                y=daily_comp["Baseline_Predicted_Hours"],
                name="Baseline Mean",
                mode="lines",
                line=dict(color="#94A3B8", width=1.5, dash="dot")
            ))
            fig_comp.update_layout(
                title="<b>Chronological Evaluation: Actual vs. Forecasted Overtime Hours</b>",
                xaxis_title="Evaluation Date (Chronological Holdout)",
                yaxis_title="Total Daily Overtime Hours",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor="rgba(255,255,255,0)",
                plot_bgcolor="rgba(255,255,255,0)"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            # Feature Importance Drivers
            st.markdown("#### 🔍 Overtime Driver Explainability (Feature Importance)")
            feat_df = summary["feature_importance"]
            fig_feat = px.bar(
                feat_df,
                x="Importance",
                y="Feature",
                orientation="h",
                color="Importance",
                color_continuous_scale="Viridis",
                title="<b>Key Factors Driving Overtime Predictions</b>"
            )
            fig_feat.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(fig_feat, use_container_width=True)

# ----------------- TAB 5: WHAT-IF SCENARIO & COST SIMULATOR -----------------
with tab5:
    st.markdown("### 💡 Step 5: What-If Workforce Scenario Simulator")
    st.caption("Simulate upcoming project workload changes or policy rate adjustments to project future budget impact.")

    if st.session_state["forecaster"] is None or st.session_state["processed_df"] is None:
        st.info("ℹ️ Please train a model in Tab 4 first to enable future scenario simulation.")
    else:
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            sim_horizon = st.slider("Forecast Horizon (Days)", min_value=3, max_value=30, value=7, step=1)
        with col_s2:
            sim_workload_pct = st.slider("Workload Shift (%)", min_value=-50, max_value=100, value=0, step=10, help="Simulate increased active project assignments")
        with col_s3:
            sim_multiplier = st.slider("Simulated OT Multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)

        generate_sim = st.button("🔮 Run Future Overtime Projection", type="primary")

        if generate_sim or st.session_state["future_forecast"] is None:
            workload_mult = 1.0 + (sim_workload_pct / 100.0)
            with st.spinner("Generating forward projections..."):
                future_df = st.session_state["forecaster"].generate_future_forecast(
                    df=st.session_state["processed_df"],
                    horizon_days=sim_horizon,
                    project_workload_multiplier=workload_mult,
                    ot_rate_multiplier=sim_multiplier
                )
                st.session_state["future_forecast"] = future_df

        if st.session_state["future_forecast"] is not None:
            f_df = st.session_state["future_forecast"]
            tot_forecast_hours = round(f_df["Forecast_Overtime_Hours"].sum(), 1)
            tot_forecast_cost = round(f_df["Estimated_Overtime_Cost"].sum(), 2)

            st.markdown("#### 📈 Projected Budget Requirements")
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                render_kpi_card("Projected Total OT", f"{tot_forecast_hours:,.1f} hrs", f"Across next {sim_horizon} days", "highlight", "🔮")
            with res_col2:
                render_kpi_card("Projected OT Payroll", f"₹{tot_forecast_cost:,.2f}", f"At {sim_multiplier}x multiplier", "warning", "💵")
            with res_col3:
                render_kpi_card("Workforce Scale", f"{f_df['Employee_ID'].nunique()} Employees", f"{f_df['Department'].nunique()} Departments", "positive", "🏢")

            # Projected Department Breakdown
            dept_proj = f_df.groupby("Department").agg({
                "Forecast_Overtime_Hours": "sum",
                "Estimated_Overtime_Cost": "sum"
            }).reset_index()

            fig_proj = px.bar(
                dept_proj,
                x="Department",
                y="Estimated_Overtime_Cost",
                color="Forecast_Overtime_Hours",
                color_continuous_scale="Blues",
                text_auto=",.0f",
                title=f"<b>Projected Overtime Cost by Department ({sim_horizon}-Day Horizon)</b>"
            )
            fig_proj.update_layout(yaxis_title="Estimated Cost (INR ₹)")
            st.plotly_chart(fig_proj, use_container_width=True)

            with st.expander("📄 View Detailed Employee Projections"):
                st.dataframe(f_df.head(100), use_container_width=True)

# ----------------- TAB 6: EXPORT & REPORTS -----------------
with tab6:
    st.markdown("### 📑 Step 6: Export Reports & Governance Documentation")
    st.caption("Download auditable CSV exports and formal executive reports per SRS FR-14 & TC-10.")

    if st.session_state["processed_df"] is None:
        st.warning("⚠️ No dataset loaded to export.")
    else:
        df_export = get_filtered_df(st.session_state["processed_df"])
        kpis_export = calculate_kpis(df_export)
        summary_metrics = st.session_state.get("forecast_results")

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.markdown("#### 📥 Download Processed & Filtered Records")
            st.download_button(
                label="⬇️ Download Filtered Historical Dataset (CSV)",
                data=dataframe_to_csv_bytes(df_export),
                file_name="employee_overtime_filtered_records.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_exp2:
            st.markdown("#### 📥 Download Future Forecast Projections")
            if st.session_state["future_forecast"] is not None:
                assumptions_dict = {
                    "model_name": "Random Forest / Gradient Boosting",
                    "multiplier": cfg_ot_multiplier,
                    "workdays_per_month": cfg_workdays,
                    "standard_hours": cfg_standard_hours
                }
                exportable_forecast = generate_forecast_export_df(st.session_state["future_forecast"], assumptions_dict)
                st.download_button(
                    label="⬇️ Download Forecast Schedule with Assumptions (CSV)",
                    data=dataframe_to_csv_bytes(exportable_forecast),
                    file_name="overtime_future_forecast_schedule.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("Generate a future projection in Tab 5 to download the forecast export.")

        st.markdown("---")
        st.markdown("#### 📋 Executive Summary Report")
        report_md = generate_executive_summary_markdown(kpis_export, summary_metrics)
        st.markdown(report_md)
        st.download_button(
            label="📄 Download Executive Summary (Markdown)",
            data=report_md.encode("utf-8"),
            file_name="overtime_forecasting_executive_summary.md",
            mime="text/markdown"
        )

# Employee Overtime Cost Forecasting System

A comprehensive, interactive web analytics and machine learning application to estimate future employee overtime hours and overtime costs, supporting workforce budgeting and scheduling decisions. Built strictly according to the **Software Requirements Specification (SRS v1.0)**.

---

## 🌟 Highlights & Key Features

1. **User Interface & Design**:
   - Modern design system with custom CSS, Google Fonts (*Plus Jakarta Sans* & *Inter*), executive KPI cards, status badges, and responsive Plotly visualizations.
   - Six dedicated workflow tabs covering ingestion, data exploration, EDA, ML forecasting, what-if simulation, and export.
2. **Data Ingestion & Integrity Validation**:
   - Drag-and-drop CSV upload with automatic schema detection and column normalization.
   - **1-Click Demo Loader**: Instantly loads the verified 3,000-record baseline dataset (100 employees across 30 days).
   - Data health diagnostics: duplicate `(Employee_ID, Date)` pairs, out-of-range hours, and attendance conflict checks (e.g. absent with working hours).
3. **Data Explorer & Table Views**:
   - **Display All Data** mode vs. sliced/paginated mode.
   - Real-time search by Employee ID, Role, Department, and Shift.
   - Column selector and statistical profiling summary.
4. **Exploratory Data Analysis (EDA) & KPIs**:
   - Real-time KPI cards: Total Overtime Hours, Estimated OT Cost (₹), Attendance Rate (%), and Top OT Department.
   - Interactive Plotly visualizations: Daily Overtime & Cost trend, Department comparison, Shift distribution donut, and Project Workload correlation boxplot.
5. **Leakage-Free Machine Learning Forecasting**:
   - **Strict Chronological Evaluation**: Splits data by time (train on past dates, evaluate on future dates) to prevent future data leakage. No random shuffling!
   - Baseline benchmark (training mean) vs. `RandomForestRegressor` and `GradientBoostingRegressor`.
   - Transparent evaluation metrics: **MAE** (Mean Absolute Error) and **RMSE** with percentage error reduction over baseline.
   - Feature importance driver chart explaining key predictive factors.
6. **What-If Scenario Simulator**:
   - Interactive sliders to project future budget impact when project workload changes or policy multipliers are adjusted.
7. **Reports & Audit**:
   - Download filtered historical records and future forecast schedules as CSV with transparent assumptions (multiplier, standard workdays, base hours).
   - Instant Executive Markdown Summary generation.

---

## 📐 Business Rules & Formulas

### 1. Hourly Rate (Derived Base Rate)
$$\text{Hourly Rate} = \frac{\text{Monthly Salary}}{\text{Standard Workdays (22)} \times \text{Standard Hours Per Day (8)}}$$
*Example: $\frac{₹60,000}{22 \times 8} = \frac{₹60,000}{176} = ₹340.91/\text{hr}$*

### 2. Overtime Hours (Decimal Hours)
$$\text{Overtime Hours} = \max(0, \text{Working Hours} - \text{Scheduled Hours (8)})$$
*(Note: 8.5 means 8 hours and 30 minutes. If Attendance = 0, Overtime = 0).*

### 3. Estimated Overtime Cost
$$\text{Overtime Cost} = \text{Overtime Hours} \times \text{Hourly Rate} \times \text{Overtime Multiplier (1.5)}$$
*Example: $3\text{ hrs} \times ₹340.91 \times 1.5 = ₹1,534.10$*

---

## 🛠️ Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| **Frontend / Web UI** | Streamlit 1.50+ | Modern dashboard layout, filters, tabs, interactive widgets |
| **Styling / Aesthetics** | Vanilla CSS & Google Fonts | Executive typography, glassmorphism badges, metric cards |
| **Data Processing** | pandas, NumPy | CSV ingestion, data validation, aggregation, sanitization |
| **Machine Learning** | scikit-learn | Time-series splitting, Random Forest, Gradient Boosting, metrics |
| **Interactive Visuals**| Plotly | Interactive area/line charts, bar charts, donut charts, boxplots |
| **Testing** | pytest | Automated test coverage for TC-01 through TC-12 |

---

## 🚀 Setup & Launch Instructions

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit Application
```bash
streamlit run app.py
```
The app will automatically open in your default browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the full pytest suite to verify validation rules, financial formulas, and anti-leakage time splitting:
```bash
pytest tests/ -v
```

### Test Coverage Highlights (Per SRS Section 10.1):
- `TC-01`: Load sample CSV (3,000 rows, 15 columns verified).
- `TC-02`: Missing mandatory columns rejected with clear error messages.
- `TC-03`: Invalid date format detection.
- `TC-04`: Decimal hours interpretation (8.5 = 8h 30m).
- `TC-05`: Overtime hours derivation ($10\text{h} - 8\text{h} = 2\text{h}$).
- `TC-06`: Overtime cost calculation ($2\text{h} \times 300 \times 1.5 = ₹900$).
- `TC-07`: Data quality warning for Absent records with Working Hours > 0.
- `TC-08`: Department & date range filtering updates KPIs consistently.
- `TC-09`: Chronological time-ordered evaluation without data leakage.
- `TC-10`: Export forecast with assumptions metadata.
- `TC-11`: Short dataset warning for 30-day horizons.
- `TC-12`: Empty dataset error handling and recovery.

---

## ⚠️ Known Limitations & Assumptions

1. **Synthetic Demo Data**: The 3,000-record dataset demonstrates the pipeline end-to-end but is synthetic data for prototyping and does not represent real payroll records.
2. **Seasonality Constraints**: A 30-day sample data window cannot establish annual or seasonal workforce cycles; the system flags this transparently in the UI.
3. **Workload Proxy**: Projects Assigned is a workload proxy; actual project deadlines and task hours can further enhance accuracy when available.

"""
Forecasting and Machine Learning Engine
Implements leakage-free chronological evaluation, baseline benchmark, Random Forest &
Gradient Boosting models, feature importance, and horizon forecasting per SRS Section 6.
"""
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

class OvertimeForecaster:
    """
    Forecasting pipeline with strict anti-leakage time splitting,
    baseline benchmarking, and feature importance explainability.
    """
    def __init__(self, model_type: str = "Random Forest"):
        self.model_type = model_type
        self.encoder = None
        self.feature_names = []
        self.cat_cols = ["Department", "Shift"]
        self.num_cols = ["Experience", "Projects_Assigned", "DayOfWeek", "IsWeekend", "Holiday"]
        self.model = None
        self.baseline_mean = 0.0
        self.training_summary = {}

    def _prepare_features(self, df: pd.DataFrame, is_training: bool = False) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        Derives time features and encodes categories safely without future leakage.
        """
        df = df.copy()

        # Derive chronological calendar features
        if "Date" in df.columns:
            date_series = pd.to_datetime(df["Date"], errors="coerce")
            df["DayOfWeek"] = date_series.dt.dayofweek.fillna(0)
            df["IsWeekend"] = df["DayOfWeek"].apply(lambda d: 1 if d >= 5 else 0)
        else:
            df["DayOfWeek"] = 0
            df["IsWeekend"] = 0

        if "Holiday" not in df.columns:
            df["Holiday"] = 0
        if "Projects_Assigned" not in df.columns:
            df["Projects_Assigned"] = 2
        if "Experience" not in df.columns:
            df["Experience"] = 5
        if "Shift" not in df.columns:
            df["Shift"] = "Morning"
        if "Department" not in df.columns:
            df["Department"] = "Production"

        # Categorical Encoding
        cat_data = df[self.cat_cols].fillna("Unknown")
        if is_training:
            self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            encoded_cats = self.encoder.fit_transform(cat_data)
            cat_feature_names = list(self.encoder.get_feature_names_out(self.cat_cols))
            self.feature_names = self.num_cols + cat_feature_names
        else:
            if self.encoder is None:
                raise ValueError("Encoder has not been fitted on training data yet.")
            encoded_cats = self.encoder.transform(cat_data)

        # Numerical Features
        num_data = df[self.num_cols].fillna(0).values

        # Combine
        X = np.hstack([num_data, encoded_cats])
        y = df["Overtime_Hours"].values if "Overtime_Hours" in df.columns else np.zeros(len(df))

        return X, y, df

    def train_and_evaluate(
        self,
        df: pd.DataFrame,
        test_ratio: float = 0.20
    ) -> Dict[str, Any]:
        """
        Splits data chronologically (train on past dates, test on latest dates)
        to prevent future data leakage. Computes Baseline vs ML model metrics.
        """
        if len(df) < 20:
            raise ValueError("Dataset is too small to build a reliable forecasting model.")

        # Sort chronologically
        df_sorted = df.sort_values("Date").reset_index(drop=True)
        unique_dates = df_sorted["Date"].unique()
        num_unique_dates = len(unique_dates)

        # Chronological split boundary
        split_date_idx = int(num_unique_dates * (1.0 - test_ratio))
        split_date = unique_dates[split_date_idx]

        train_mask = df_sorted["Date"] < split_date
        test_mask = df_sorted["Date"] >= split_date

        train_df = df_sorted[train_mask]
        test_df = df_sorted[test_mask]

        if len(train_df) == 0 or len(test_df) == 0:
            # Fallback if dates are identical
            cut = int(len(df_sorted) * (1.0 - test_ratio))
            train_df = df_sorted.iloc[:cut]
            test_df = df_sorted.iloc[cut:]
            split_date = test_df["Date"].iloc[0]

        # Prepare features
        X_train, y_train, _ = self._prepare_features(train_df, is_training=True)
        X_test, y_test, processed_test_df = self._prepare_features(test_df, is_training=False)

        # Baseline: Predict training set mean
        self.baseline_mean = float(np.mean(y_train))
        y_pred_baseline = np.full(shape=y_test.shape, fill_value=self.baseline_mean)

        baseline_mae = round(float(mean_absolute_error(y_test, y_pred_baseline)), 3)
        baseline_rmse = round(float(root_mean_squared_error(y_test, y_pred_baseline)), 3)

        # Fit Selected ML Model
        if self.model_type == "Gradient Boosting":
            self.model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        else:
            self.model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)

        self.model.fit(X_train, y_train)

        # Evaluate on Test Data
        y_pred_model = np.maximum(0.0, self.model.predict(X_test)).round(2)
        model_mae = round(float(mean_absolute_error(y_test, y_pred_model)), 3)
        model_rmse = round(float(root_mean_squared_error(y_test, y_pred_model)), 3)

        # Feature Importance
        importances = self.model.feature_importances_
        feature_importance_df = pd.DataFrame({
            "Feature": self.feature_names,
            "Importance": importances
        }).sort_values("Importance", ascending=False).head(10)

        # Test Results Comparison Table
        comparison_df = processed_test_df[["Date", "Employee_ID", "Department", "Shift", "Overtime_Hours"]].copy()
        comparison_df.rename(columns={"Overtime_Hours": "Actual_Overtime_Hours"}, inplace=True)
        comparison_df["Predicted_Overtime_Hours"] = y_pred_model
        comparison_df["Baseline_Predicted_Hours"] = round(self.baseline_mean, 2)
        comparison_df["Hourly_Rate"] = processed_test_df.get("Hourly_Rate", 250.0)
        comparison_df["Estimated_Predicted_Cost"] = (
            comparison_df["Predicted_Overtime_Hours"] * comparison_df["Hourly_Rate"] * 1.5
        ).round(2)

        # Aggregated daily comparison for visual plotting
        daily_comp = comparison_df.groupby("Date").agg({
            "Actual_Overtime_Hours": "sum",
            "Predicted_Overtime_Hours": "sum",
            "Baseline_Predicted_Hours": "sum"
        }).reset_index()

        self.training_summary = {
            "total_samples": len(df_sorted),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "split_date": split_date,
            "span_days": num_unique_dates,
            "baseline_mae": baseline_mae,
            "baseline_rmse": baseline_rmse,
            "model_mae": model_mae,
            "model_rmse": model_rmse,
            "mae_improvement_pct": round(((baseline_mae - model_mae) / max(0.001, baseline_mae)) * 100, 1),
            "feature_importance": feature_importance_df,
            "daily_comparison": daily_comp,
            "detailed_comparison": comparison_df.head(50),
            "warning": "30 days of data is suitable for short-horizon operational planning, but does not support long-term annual seasonality." if num_unique_dates <= 35 else ""
        }
        return self.training_summary

    def generate_future_forecast(
        self,
        df: pd.DataFrame,
        horizon_days: int = 7,
        project_workload_multiplier: float = 1.0,
        ot_rate_multiplier: float = 1.5
    ) -> pd.DataFrame:
        """
        Projects future overtime hours and costs across employees/departments for the requested horizon.
        """
        if self.model is None or self.encoder is None:
            raise ValueError("Forecasting model must be trained before generating future forecasts.")

        # Determine start of forecast horizon
        last_date = pd.to_datetime(df["Date"]).max()
        future_dates = [last_date + timedelta(days=d) for d in range(1, horizon_days + 1)]

        # Unique active employees to project
        emp_profiles = df.drop_duplicates(subset=["Employee_ID"]).copy()

        future_records = []
        for f_date in future_dates:
            date_str = f_date.strftime("%Y-%m-%d")
            day_of_week = f_date.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            is_holiday = 1 if day_of_week == 6 else 0

            for _, emp in emp_profiles.iterrows():
                base_projects = float(emp.get("Projects_Assigned", 2))
                adj_projects = max(1, int(round(base_projects * project_workload_multiplier)))

                future_records.append({
                    "Date": date_str,
                    "Employee_ID": emp["Employee_ID"],
                    "Department": emp["Department"],
                    "Employee_Role": emp.get("Employee_Role", "General"),
                    "Shift": emp["Shift"],
                    "Experience": emp.get("Experience", 5),
                    "Projects_Assigned": adj_projects,
                    "Hourly_Rate": emp.get("Hourly_Rate", 250.0),
                    "DayOfWeek": day_of_week,
                    "IsWeekend": is_weekend,
                    "Holiday": is_holiday
                })

        future_df = pd.DataFrame(future_records)
        X_future, _, _ = self._prepare_features(future_df, is_training=False)

        predicted_hours = np.maximum(0.0, self.model.predict(X_future)).round(2)
        future_df["Forecast_Overtime_Hours"] = predicted_hours
        future_df["Estimated_Overtime_Cost"] = (
            future_df["Forecast_Overtime_Hours"] * future_df["Hourly_Rate"] * ot_rate_multiplier
        ).round(2)

        return future_df

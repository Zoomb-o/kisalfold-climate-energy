"""
train_demand_model.py
---------------------
Trains an XGBoost model to predict daily electricity demand
from climate variables. Uses SHAP for interpretability.

Output:
  results/figures/model_performance.png
  results/figures/shap_summary.png
  results/tables/model_metrics.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pathlib import Path

DATA_PATH = Path("data/processed/master_dataset.csv")
FIG_DIR   = Path("results/figures")
TAB_DIR   = Path("results/tables")
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "temp_mean_c", "temp_max_c", "temp_min_c",
    "HDD", "CDD",
    "wind_mean_m_s", "solar_rad_j_m2", "precip_mm",
    "month", "weekday", "is_weekend",
]
TARGET = "load_mean_MW"

# Train on 2015-2021, test on 2022-2024
TRAIN_END = "2021-12-31"
TEST_START = "2022-01-01"


def main():
    print("Loading master dataset...")
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])

    train = df[df["date"] <= TRAIN_END]
    test  = df[df["date"] >= TEST_START]

    X_train = train[FEATURES]
    y_train = train[TARGET]
    X_test  = test[FEATURES]
    y_test  = test[TARGET]

    print(f"Train: {len(train)} days ({train.date.min().date()} to {train.date.max().date()})")
    print(f"Test:  {len(test)} days ({test.date.min().date()} to {test.date.max().date()})")

    print("\nTraining XGBoost model...")
    model = xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # Metrics
    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

    print(f"\nTest set performance:")
    print(f"  MAE  = {mae:.1f} MW")
    print(f"  RMSE = {rmse:.1f} MW")
    print(f"  R²   = {r2:.4f}")
    print(f"  MAPE = {mape:.2f}%")

    metrics = pd.DataFrame([{
        "MAE_MW": round(mae, 1),
        "RMSE_MW": round(rmse, 1),
        "R2": round(r2, 4),
        "MAPE_pct": round(mape, 2),
        "train_days": len(train),
        "test_days": len(test),
    }])
    metrics.to_csv(TAB_DIR / "model_metrics.csv", index=False)

    # Plot 1 — predicted vs actual
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("XGBoost Demand Model — Test Set Performance (2022–2024)", fontsize=13)

    axes[0].scatter(y_test, y_pred, alpha=0.3, s=10, color="#534AB7")
    lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
    axes[0].plot(lims, lims, "r--", linewidth=1)
    axes[0].set_xlabel("Actual load (MW)")
    axes[0].set_ylabel("Predicted load (MW)")
    axes[0].set_title(f"Predicted vs Actual\nR² = {r2:.4f}  RMSE = {rmse:.0f} MW")
    axes[0].grid(True, alpha=0.3)

    test_plot = test.copy()
    test_plot["predicted"] = y_pred
    sample = test_plot[test_plot["date"].dt.year == 2023]
    axes[1].plot(sample["date"], sample["load_mean_MW"],
                 label="Actual", color="#D85A30", linewidth=1)
    axes[1].plot(sample["date"], sample["predicted"],
                 label="Predicted", color="#534AB7", linewidth=1, alpha=0.8)
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Load (MW)")
    axes[1].set_title("Actual vs Predicted — 2023")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "model_performance.png", dpi=150, bbox_inches="tight")
    print(f"\nSaved: results/figures/model_performance.png")
    plt.show()

    # Plot 2 — SHAP
    print("\nCalculating SHAP values...")
    explainer = shap.Explainer(model)
    shap_values = explainer(X_test)

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    shap.plots.beeswarm(shap_values, max_display=11, show=False)
    plt.title("SHAP Feature Importance — What drives electricity demand?")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "shap_summary.png", dpi=150, bbox_inches="tight")
    print("Saved: results/figures/shap_summary.png")
    plt.show()

    print("\nDone! Model training complete.")


if __name__ == "__main__":
    main()
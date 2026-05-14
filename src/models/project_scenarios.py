"""
project_scenarios.py
--------------------
Uses the trained XGBoost model to project electricity demand
under three CMIP6/IPCC AR6 warming scenarios to 2100.

Also estimates transmission losses under each scenario.

Output:
  data/processed/demand_projections.csv
  results/figures/demand_projections.png
  results/figures/loss_amplification.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from pathlib import Path

DATA_PATH = Path("data/processed/master_dataset.csv")
PROJ_PATH = Path("data/processed/cmip6_projections.csv")
OUT_DIR   = Path("results/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "temp_mean_c", "temp_max_c", "temp_min_c",
    "temp_squared", "temp_roll7",
    "HDD", "CDD",
    "wind_mean_m_s", "solar_rad_j_m2", "precip_mm",
    "month", "weekday", "is_weekend",
    "day_of_year", "year_trend",
    "temp_x_weekend",
]

# ENTSO-E European average transmission loss rate ~6.5%
# Loss rate increases ~0.4% per degree C above baseline
# Source: ENTSO-E Statistical Factsheet 2022
BASE_LOSS_RATE = 0.065
LOSS_TEMP_SENSITIVITY = 0.004
BASELINE_TEMP = 11.5  # ERA5 1991-2020 mean for Kisalfold


def prepare_features(df):
    df = df.copy()
    df["temp_max_c"]     = df["temp_mean_c"] + 4.0   # seasonal spread proxy
    df["temp_min_c"]     = df["temp_mean_c"] - 4.0
    df["HDD"]            = (15.5 - df["temp_mean_c"]).clip(lower=0) * 30
    df["CDD"]            = (df["temp_mean_c"] - 18.0).clip(lower=0) * 30
    df["temp_squared"]   = df["temp_mean_c"] ** 2
    df["temp_roll7"]     = df["temp_mean_c"]
    df["day_of_year"]    = df["month"] * 30
    df["temp_x_weekend"] = df["temp_mean_c"] * 0.28
    df["is_weekend"]     = 0
    df["weekday"]        = 2
    df["wind_mean_m_s"]  = 3.5
    df["solar_rad_j_m2"] = 12_000_000
    df["precip_mm"]      = 2.0
    return df


def train_model():
    df = pd.read_csv(DATA_PATH)
    df["date"]           = pd.to_datetime(df["date"])
    df["temp_squared"]   = df["temp_mean_c"] ** 2
    df["day_of_year"]    = df["date"].dt.dayofyear
    df["year_trend"]     = df["date"].dt.year - 2015
    df["temp_x_weekend"] = df["temp_mean_c"] * df["is_weekend"]
    df                   = df.sort_values("date")
    df["temp_roll7"]     = df["temp_mean_c"].rolling(7, min_periods=1).mean()

    train = df[df["date"] <= "2021-12-31"]
    model = xgb.XGBRegressor(
        n_estimators=1000, learning_rate=0.03, max_depth=5,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        random_state=42, verbosity=0,
    )
    model.fit(train[FEATURES], train["load_mean_MW"], verbose=False)
    return model


def project_demand(model, proj_df):
    records = []
    for scenario in proj_df["scenario"].unique():
        s = proj_df[proj_df["scenario"] == scenario].copy()

        for year in sorted(s["year"].unique()):
            yr = s[s["year"] == year].copy()
            yr["year_trend"] = year - 2015
            yr = prepare_features(yr)

            # Predict monthly load then aggregate to annual
            yr["load_MW"] = model.predict(yr[FEATURES])
            annual_load   = yr["load_MW"].mean()

            # Transmission loss amplification
            annual_temp   = yr["temp_mean_c"].mean()
            temp_delta    = max(annual_temp - BASELINE_TEMP, 0)
            loss_rate     = BASE_LOSS_RATE + LOSS_TEMP_SENSITIVITY * temp_delta
            extra_loss_pct = (loss_rate - BASE_LOSS_RATE) * 100

            # Energy that must be generated to deliver the demanded load
            required_gen  = annual_load / (1 - loss_rate)
            wasted_mw     = required_gen - annual_load

            records.append({
                "scenario":       scenario,
                "year":           year,
                "load_mean_MW":   round(annual_load, 1),
                "loss_rate_pct":  round(loss_rate * 100, 3),
                "extra_loss_pct": round(extra_loss_pct, 3),
                "required_gen_MW": round(required_gen, 1),
                "wasted_MW":      round(wasted_mw, 1),
                "temp_mean_c":    round(annual_temp, 3),
            })

    return pd.DataFrame(records)


def plot_demand(df_proj, df_hist):
    colors = {
        "SSP1-2.6": "#2196F3",
        "SSP2-4.5": "#FF9800",
        "SSP5-8.5": "#F44336",
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "Projected Hungarian Electricity Demand Under Climate Scenarios",
        fontsize=13
    )

    # Historical baseline
    hist_annual = df_hist.groupby("year")["load_mean_MW"].mean().reset_index()

    for scenario, color in colors.items():
        s = df_proj[df_proj["scenario"] == scenario]
        axes[0].plot(s["year"], s["load_mean_MW"],
                     color=color, linewidth=2, label=scenario)
        axes[1].plot(s["year"], s["wasted_MW"],
                     color=color, linewidth=2, label=scenario)

    axes[0].plot(hist_annual["year"], hist_annual["load_mean_MW"],
                 color="#333333", linewidth=1.5, label="ENTSO-E observed")
    axes[0].axvline(2024, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Annual mean load (MW)")
    axes[0].set_title("Projected electricity demand")
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)

    axes[1].axvline(2024, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Wasted energy (MW equivalent)")
    axes[1].set_title("Energy lost to temperature-driven\ntransmission losses")
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "demand_projections.png", dpi=150, bbox_inches="tight")
    print("Saved: results/figures/demand_projections.png")
    plt.show()


def plot_loss_amplification(df_proj):
    colors = {
        "SSP1-2.6": "#2196F3",
        "SSP2-4.5": "#FF9800",
        "SSP5-8.5": "#F44336",
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(
        "Infrastructure Loss Amplification Effect\n"
        "Extra transmission losses due to climate warming above 2015 baseline",
        fontsize=12
    )

    for scenario, color in colors.items():
        s = df_proj[df_proj["scenario"] == scenario]
        ax.fill_between(s["year"], s["extra_loss_pct"],
                        alpha=0.2, color=color)
        ax.plot(s["year"], s["extra_loss_pct"],
                color=color, linewidth=2, label=scenario)

    ax.set_xlabel("Year")
    ax.set_ylabel("Extra transmission loss (%)")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "loss_amplification.png", dpi=150, bbox_inches="tight")
    print("Saved: results/figures/loss_amplification.png")
    plt.show()


def main():
    print("Training demand model...")
    model = train_model()

    print("Loading projections...")
    proj = pd.read_csv(PROJ_PATH)

    print("Projecting demand under each scenario...")
    df_proj = project_demand(model, proj)

    hist = pd.read_csv(DATA_PATH)
    hist["date"] = pd.to_datetime(hist["date"])
    hist["year"] = hist["date"].dt.year

    df_proj.to_csv("data/processed/demand_projections.csv", index=False)
    print("Saved: data/processed/demand_projections.csv")

    print("\nKey results by scenario (2050):")
    for scenario in df_proj["scenario"].unique():
        s2050 = df_proj[
            (df_proj["scenario"] == scenario) &
            (df_proj["year"] == 2050)
        ].iloc[0]
        print(f"\n  {scenario}:")
        print(f"    Projected load:     {s2050['load_mean_MW']:.0f} MW")
        print(f"    Loss rate:          {s2050['loss_rate_pct']:.2f}%")
        print(f"    Extra loss:         {s2050['extra_loss_pct']:.3f}%")
        print(f"    Wasted energy:      {s2050['wasted_MW']:.0f} MW")

    plot_demand(df_proj, hist)
    plot_loss_amplification(df_proj)
    print("\nDone!")


if __name__ == "__main__":
    main()
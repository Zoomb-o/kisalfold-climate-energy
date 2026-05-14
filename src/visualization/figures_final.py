"""
figures_final.py
----------------
Generates all publication-quality figures for the paper.

Run from project root:
  python src/visualization/figures_final.py
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import shap
import xgboost as xgb
from pathlib import Path

sys.path.insert(0, "src/visualization")

# ── Style ────────────────────────────────────────────────────────────────────
SCENARIO_COLORS = {
    "SSP1-2.6": "#1A85FF",
    "SSP2-4.5": "#FFA500",
    "SSP5-8.5": "#D41159",
}
SEASON_COLORS = {
    "Winter": "#1A85FF",
    "Spring": "#4CAF50",
    "Summer": "#D41159",
    "Autumn": "#FF8C00",
}
OBSERVED_COLOR = "#222222"
HIGHLIGHT      = "#534AB7"

mpl.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,
    "legend.fontsize":   10,
    "figure.dpi":        150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.color":        "#E0E0E0",
    "grid.linewidth":    0.8,
    "axes.axisbelow":    True,
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "savefig.bbox":      "tight",
    "savefig.dpi":       300,
})

OUT = Path("results/figures")
OUT.mkdir(parents=True, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
era5   = pd.read_csv("data/processed/era5_daily.csv")
master = pd.read_csv("data/processed/master_dataset.csv")
proj   = pd.read_csv("data/processed/cmip6_projections.csv")
d_proj = pd.read_csv("data/processed/demand_projections.csv")

era5["date"]   = pd.to_datetime(era5["date"])
master["date"] = pd.to_datetime(master["date"])
era5["year"]   = era5["date"].dt.year
master["year"] = master["date"].dt.year


# ── Figure 1: Temperature vs Demand ──────────────────────────────────────────
def fig_temp_vs_demand():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        "Figure 1 — Surface Temperature vs Electricity Demand, Hungary 2015–2024",
        fontsize=12, fontweight="bold"
    )

    for season, color in SEASON_COLORS.items():
        s = master[master["season"] == season]
        axes[0].scatter(s["temp_mean_c"], s["load_mean_MW"],
                        c=color, alpha=0.35, s=9, label=season, linewidths=0)

    axes[0].set_xlabel("Daily mean temperature (°C)")
    axes[0].set_ylabel("Daily mean load (MW)")
    axes[0].set_title("(a) Daily observations by season")
    axes[0].legend(markerscale=2, framealpha=0.9)

    monthly = master.groupby(["year", "month"]).agg(
        temp=("temp_mean_c", "mean"),
        load=("load_mean_MW", "mean")
    ).reset_index()

    axes[1].scatter(monthly["temp"], monthly["load"],
                    color=HIGHLIGHT, alpha=0.65, s=22, linewidths=0)

    from statsmodels.nonparametric.smoothers_lowess import lowess
    sorted_monthly = monthly.sort_values("temp")
    smoothed = lowess(sorted_monthly["load"], sorted_monthly["temp"], frac=0.4)
    axes[1].plot(smoothed[:, 0], smoothed[:, 1],
                 color="#D41159", linewidth=2.5, label="LOWESS trend")

    # Annotate minimum
    min_idx = smoothed[:, 1].argmin()
    x_min   = smoothed[min_idx, 0]
    y_min   = smoothed[min_idx, 1]
    axes[1].annotate(
        f"Min. demand\n~{x_min:.0f}°C",
        xy=(x_min, y_min),
        xytext=(x_min + 5, y_min + 180),
        arrowprops=dict(arrowstyle="->", color="gray"),
        fontsize=9, color="gray"
    )

    axes[1].set_xlabel("Monthly mean temperature (°C)")
    axes[1].set_ylabel("Monthly mean load (MW)")
    axes[1].set_title("(b) Monthly aggregates with fitted U-curve")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(OUT / "fig1_temp_vs_demand.png")
    print("Saved: fig1_temp_vs_demand.png")
    plt.close()


# ── Figure 2: Climate Trends ──────────────────────────────────────────────────
def fig_climate_trends():
    annual = era5.groupby("year").agg(
        temp=("temp_mean_c", "mean"),
        HDD=("HDD", "sum"),
        CDD=("CDD", "sum"),
    ).reset_index()

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        "Figure 2 — Kisalföld Climate Trends 1970–2024 (ERA5 Reanalysis)",
        fontsize=12, fontweight="bold"
    )

    configs = [
        ("temp", "Annual mean temperature (°C)", "#D41159", "°C"),
        ("HDD",  "Annual Heating Degree Days",   "#1A85FF", "days"),
        ("CDD",  "Annual Cooling Degree Days",   "#D41159", "days"),
    ]
    labels = ["(a)", "(b)", "(c)"]

    for ax, (col, ylabel, color, unit), label in zip(axes, configs, labels):
        ax.scatter(annual["year"], annual[col],
                   color=color, alpha=0.6, s=22, linewidths=0, zorder=3)
        z = np.polyfit(annual["year"], annual[col], 1)
        p = np.poly1d(z)
        ax.plot(annual["year"], p(annual["year"]),
                color=color, linewidth=2, zorder=4)
        trend = z[0] * 10
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{label} {ylabel}\nTrend: {trend:+.2f} {unit} per decade")

    plt.tight_layout()
    plt.savefig(OUT / "fig2_climate_trends.png")
    print("Saved: fig2_climate_trends.png")
    plt.close()


# ── Figure 3: Climate Projections ─────────────────────────────────────────────
def fig_projections():
    ann_proj = proj.groupby(["scenario", "year"]).agg(
        temp=("temp_mean_c", "mean"),
        HDD=("HDD_monthly", "sum"),
        CDD=("CDD_monthly", "sum"),
    ).reset_index()

    hist = era5.groupby("year").agg(
        temp=("temp_mean_c", "mean"),
        HDD=("HDD", "sum"),
        CDD=("CDD", "sum"),
    ).reset_index()
    hist = hist[hist["year"] >= 1970]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
    fig.suptitle(
        "Figure 3 — Kisalföld Climate Projections 1970–2100 (ERA5 + IPCC AR6)",
        fontsize=12, fontweight="bold"
    )

    configs = [
        ("temp", "Annual mean temperature (°C)"),
        ("HDD",  "Annual Heating Degree Days"),
        ("CDD",  "Annual Cooling Degree Days"),
    ]
    labels = ["(a)", "(b)", "(c)"]

    for ax, (col, ylabel), label in zip(axes, configs, labels):
        ax.plot(hist["year"], hist[col], color=OBSERVED_COLOR,
                linewidth=1.8, label="ERA5 observed", zorder=5)
        for scenario, color in SCENARIO_COLORS.items():
            s = ann_proj[ann_proj["scenario"] == scenario]
            ax.plot(s["year"], s[col], color=color,
                    linewidth=2, label=scenario, zorder=4)
        ax.axvline(2024, color="gray", linestyle="--",
                   linewidth=1, alpha=0.6)
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{label} {ylabel}")
        if col == "temp":
            ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT / "fig3_projections.png")
    print("Saved: fig3_projections.png")
    plt.close()


# ── Figure 4: Demand Composition ─────────────────────────────────────────────
def fig_demand_composition():
    ann_proj = proj.groupby(["scenario", "year"]).agg(
        HDD=("HDD_monthly", "sum"),
        CDD=("CDD_monthly", "sum"),
    ).reset_index()

    base = ann_proj[ann_proj["year"] == 2025].set_index("scenario")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
    fig.suptitle(
        "Figure 4 — Energy Demand Composition Shift Under Climate Scenarios",
        fontsize=12, fontweight="bold"
    )

    for scenario, color in SCENARIO_COLORS.items():
        s = ann_proj[ann_proj["scenario"] == scenario]
        b = base.loc[scenario]
        hdd_delta = s["HDD"].values - b["HDD"]
        cdd_delta = s["CDD"].values - b["CDD"]
        net = cdd_delta * 8 + hdd_delta * 5

        axes[0].plot(s["year"], s["HDD"], color=color, linewidth=2, label=scenario)
        axes[1].plot(s["year"], s["CDD"], color=color, linewidth=2, label=scenario)
        axes[2].plot(s["year"], net, color=color, linewidth=2, label=scenario)
        axes[2].fill_between(s["year"], net, alpha=0.12, color=color)

    axes[2].axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    axes[2].annotate(
        "Heating savings\nexceed cooling gains",
        xy=(2050, -350), fontsize=9, color="gray", ha="center"
    )
    axes[2].annotate(
        "SSP5-8.5: cooling\novertakes heating savings",
        xy=(2082, -30), fontsize=9, color="#D41159", ha="center"
    )

    configs = [
        ("(a) Heating Degree Days",     "Annual HDD"),
        ("(b) Cooling Degree Days",     "Annual CDD"),
        ("(c) Net demand shift vs 2025","MW equivalent"),
    ]
    for ax, (title, ylabel) in zip(axes, configs):
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT / "fig4_demand_composition.png")
    print("Saved: fig4_demand_composition.png")
    plt.close()


# ── Figure 5: Transmission Loss Amplification ─────────────────────────────────
def fig_loss_amplification():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        "Figure 5 — Temperature-Driven Transmission Loss Amplification",
        fontsize=12, fontweight="bold"
    )

    for scenario, color in SCENARIO_COLORS.items():
        s = d_proj[d_proj["scenario"] == scenario]
        axes[0].plot(s["year"], s["loss_rate_pct"],
                     color=color, linewidth=2, label=scenario)
        axes[1].plot(s["year"], s["wasted_MW"],
                     color=color, linewidth=2, label=scenario)
        axes[1].fill_between(s["year"], s["wasted_MW"],
                             alpha=0.12, color=color)

    axes[0].axhline(6.5, color="gray", linestyle="--",
                    linewidth=1, label="2015 baseline (6.5%)")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Transmission loss rate (%)")
    axes[0].set_title("(a) Projected grid transmission loss rate")
    axes[0].legend(fontsize=9)

    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Energy wasted (MW equivalent)")
    axes[1].set_title("(b) Annual energy lost to excess transmission losses")
    axes[1].legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT / "fig5_loss_amplification.png")
    print("Saved: fig5_loss_amplification.png")
    plt.close()


# ── Figure 6: SHAP ────────────────────────────────────────────────────────────
def fig_shap():
    FEATURES = [
        "temp_mean_c", "temp_max_c", "temp_min_c",
        "temp_squared", "temp_roll7", "HDD", "CDD",
        "wind_mean_m_s", "solar_rad_j_m2", "precip_mm",
        "month", "weekday", "is_weekend",
        "day_of_year", "year_trend", "temp_x_weekend",
    ]
    LABELS = {
        "temp_mean_c":    "Daily mean temperature",
        "temp_max_c":     "Daily max temperature",
        "temp_min_c":     "Daily min temperature",
        "temp_squared":   "Temperature² (non-linearity)",
        "temp_roll7":     "7-day rolling temperature",
        "HDD":            "Heating Degree Days",
        "CDD":            "Cooling Degree Days",
        "wind_mean_m_s":  "Wind speed",
        "solar_rad_j_m2": "Solar radiation",
        "precip_mm":      "Precipitation",
        "month":          "Month of year",
        "weekday":        "Day of week",
        "is_weekend":     "Weekend flag",
        "day_of_year":    "Day of year (seasonality)",
        "year_trend":     "Long-term demand trend",
        "temp_x_weekend": "Temperature × Weekend interaction",
    }

    df = master.copy()
    df["temp_squared"]   = df["temp_mean_c"] ** 2
    df["day_of_year"]    = df["date"].dt.dayofyear
    df["year_trend"]     = df["date"].dt.year - 2015
    df["temp_x_weekend"] = df["temp_mean_c"] * df["is_weekend"]
    df = df.sort_values("date")
    df["temp_roll7"]     = df["temp_mean_c"].rolling(7, min_periods=1).mean()

    train = df[df["date"] <= "2021-12-31"]
    test  = df[df["date"] >= "2022-01-01"]

    model = xgb.XGBRegressor(
        n_estimators=1000, learning_rate=0.03, max_depth=5,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        random_state=42, verbosity=0,
    )
    model.fit(train[FEATURES], train["load_mean_MW"], verbose=False)

    X_test = test[FEATURES].copy()
    X_test.columns = [LABELS[c] for c in FEATURES]

    print("Calculating SHAP values...")
    explainer   = shap.Explainer(model, feature_names=list(X_test.columns))
    shap_values = explainer(X_test)

    plt.figure(figsize=(11, 8))
    shap.plots.beeswarm(shap_values, max_display=16, show=False)
    plt.title(
        "Figure 6 — SHAP Feature Importance: Drivers of Hungarian Electricity Demand",
        fontsize=12, fontweight="bold", pad=15
    )
    plt.tight_layout()
    plt.savefig(OUT / "fig6_shap.png", dpi=300, bbox_inches="tight")
    print("Saved: fig6_shap.png")
    plt.close()


# ── Run all ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating publication figures...\n")
    fig_temp_vs_demand()
    fig_climate_trends()
    fig_projections()
    fig_demand_composition()
    fig_loss_amplification()
    fig_shap()
    print("\nAll 6 figures saved to results/figures/")
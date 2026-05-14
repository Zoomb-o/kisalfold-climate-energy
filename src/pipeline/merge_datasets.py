"""
merge_datasets.py
-----------------
Merges ERA5 daily climate data with ENTSO-E hourly load data
into a single master dataset for analysis.

Output: data/processed/master_dataset.csv
"""

import pandas as pd
from pathlib import Path

ERA5_PATH   = Path("data/processed/era5_daily.csv")
ENTSO_DIR   = Path("data/raw/entso_e")
OUT_PATH    = Path("data/processed/master_dataset.csv")


def load_entso_e():
    """Load and aggregate ENTSO-E hourly load to daily."""
    dfs = []
    for f in sorted(ENTSO_DIR.glob("entso_e_load_HU_*.csv")):
        df = pd.read_csv(f)
        df.columns = ["timestamp", "load_MW"]
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["date"] = df["timestamp"].dt.date
        dfs.append(df)

    load = pd.concat(dfs)
    daily = (
        load.groupby("date")
        .agg(
            load_mean_MW=("load_MW", "mean"),
            load_max_MW=("load_MW", "max"),
            load_min_MW=("load_MW", "min"),
            n_hours=("load_MW", "count"),
        )
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def load_era5():
    df = pd.read_csv(ERA5_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


def main():
    print("Loading ERA5 daily data...")
    era5 = load_era5()
    print(f"  {len(era5)} days ({era5.date.min().date()} to {era5.date.max().date()})")

    print("Loading and aggregating ENTSO-E load data...")
    load = load_entso_e()
    print(f"  {len(load)} days ({load.date.min().date()} to {load.date.max().date()})")

    print("Merging...")
    master = pd.merge(era5, load, on="date", how="inner")

    # Add time features useful for the model
    master["year"]    = master["date"].dt.year
    master["month"]   = master["date"].dt.month
    master["season"]  = master["month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring",  4: "Spring", 5: "Spring",
        6: "Summer",  7: "Summer", 8: "Summer",
        9: "Autumn", 10: "Autumn", 11: "Autumn",
    })
    master["weekday"] = master["date"].dt.weekday
    master["is_weekend"] = (master["weekday"] >= 5).astype(int)

    master = master.sort_values("date").reset_index(drop=True)
    master.to_csv(OUT_PATH, index=False)

    print(f"\nDone! Master dataset: {len(master)} days")
    print(f"Date range: {master.date.min().date()} to {master.date.max().date()}")
    print(f"Columns: {list(master.columns)}")
    print(f"\nSample:")
    print(master[["date","temp_mean_c","HDD","CDD","load_mean_MW","season"]].tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
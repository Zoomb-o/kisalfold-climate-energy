"""
fetch_soundings_wyoming.py
--------------------------
Downloads historical twice-daily sounding data for WMO station 12843
(Budapest/Pestszentlőrinc) from the University of Wyoming upper-air archive.

Output: data/raw/soundings/wyoming/wyoming_YYYY_MM.csv
        data/processed/soundings_wyoming_daily.csv
"""

import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from siphon.simplewebservice.wyoming import WyomingUpperAir

STATION = "12843"
OUT_DIR = Path("data/raw/soundings/wyoming")
OUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2010
START_MONTH = 1
END = datetime.utcnow()
HOURS = [0, 12]


def fetch_month(year, month):
    out_file = OUT_DIR / f"wyoming_{year}_{month:02d}.csv"
    if out_file.exists():
        print(f"  Already have {year}-{month:02d}, skipping.")
        return pd.read_csv(out_file).to_dict("records")

    records = []
    date = datetime(year, month, 1)
    while date.month == month and date <= END:
        for hour in HOURS:
            dt = date.replace(hour=hour)
            if dt > END:
                break
            try:
                df = WyomingUpperAir.request_data(dt, STATION)
                if df is not None and not df.empty:
                    surface = df.iloc[0]
                    records.append({
                        "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "date": dt.strftime("%Y-%m-%d"),
                        "hour_utc": hour,
                        "pressure_hPa": surface["pressure"],
                        "height_m": surface["height"],
                        "temp_c": surface["temperature"],
                        "dewpoint_c": surface["dewpoint"],
                        "wind_dir_deg": surface["direction"],
                        "wind_speed_m_s": surface["speed"],
                    })
            except Exception as e:
                print(f"    Missing: {dt.strftime('%Y-%m-%d %H')}Z — {e}")
            time.sleep(0.5)
        date += timedelta(days=1)

    if records:
        pd.DataFrame(records).to_csv(out_file, index=False)
        print(f"  ✓ {year}-{month:02d}  →  {len(records)} soundings")
    else:
        print(f"  ✗ {year}-{month:02d}  →  no data")
    return records


def main():
    print(f"Fetching historical soundings for WMO {STATION} (Budapest/Pestszentlőrinc)")
    print(f"Period: {START_YEAR}-{START_MONTH:02d} to {END.strftime('%Y-%m')}")
    print("Saves each month as it goes — safe to stop and resume anytime.\n")

    all_records = []
    year, month = START_YEAR, START_MONTH

    while (year, month) <= (END.year, END.month):
        print(f"Processing {year}-{month:02d}...")
        all_records.extend(fetch_month(year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1

    if not all_records:
        print("No records retrieved.")
        return

    df = pd.DataFrame(all_records)
    df["date"] = pd.to_datetime(df["date"])

    daily = (
        df.groupby("date")
        .agg(
            temp_mean_c=("temp_c", "mean"),
            temp_max_c=("temp_c", "max"),
            temp_min_c=("temp_c", "min"),
            wind_mean_m_s=("wind_speed_m_s", "mean"),
            n_soundings=("temp_c", "count"),
        )
        .reset_index()
    )

    daily["HDD"] = (15.5 - daily["temp_mean_c"]).clip(lower=0)
    daily["CDD"] = (daily["temp_mean_c"] - 18.0).clip(lower=0)

    out_path = Path("data/processed/soundings_wyoming_daily.csv")
    daily.to_csv(out_path, index=False)

    print(f"\nDone! {len(df)} soundings, {len(daily)} days")
    print(f"Range: {daily['date'].min().date()} → {daily['date'].max().date()}")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
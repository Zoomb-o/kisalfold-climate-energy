"""
process_soundings.py
--------------------
Reads all sounding CSVs from data/raw/soundings/ and extracts
surface-level variables relevant to the energy-climate study.

Output: data/processed/soundings_surface.csv

Expected filename format: sounding_YYYY-MM-DD_HHZ.csv
Expected columns: PRES, HGHT, TEMP, DWPT, RELH, MIXR, DRCT, SPED, THTA, THTE, THTV
"""

import os
import re
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw/soundings")
OUT_FILE = Path("data/processed/soundings_surface.csv")

FILENAME_PATTERN = re.compile(r"sounding_(\d{4}-\d{2}-\d{2})_(\d{2})Z\.csv")


def extract_surface(filepath: Path, date: str, hour: int) -> dict | None:
    """Extract the lowest pressure level (surface) row from a sounding file."""
    try:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()

        # Surface = row with highest pressure value
        surface = df.loc[df["PRES"].idxmax()]

        return {
            "datetime": pd.Timestamp(f"{date} {hour:02d}:00:00", tz="UTC"),
            "date": date,
            "hour_utc": hour,
            "pressure_hPa": surface["PRES"],
            "height_m": surface["HGHT"],
            "temp_c": surface["TEMP"],
            "dewpoint_c": surface["DWPT"],
            "rel_humidity_pct": surface["RELH"],
            "mixing_ratio_g_kg": surface["MIXR"],
            "wind_dir_deg": surface["DRCT"],
            "wind_speed_m_s": surface["SPED"],
        }
    except Exception as e:
        print(f"  Warning: could not parse {filepath.name}: {e}")
        return None


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    records = []
    files = sorted(RAW_DIR.glob("*.csv"))

    if not files:
        print(f"No sounding files found in {RAW_DIR}/")
        print("Place your sounding CSVs there with the naming format:")
        print("  sounding_YYYY-MM-DD_HHZ.csv  (e.g. sounding_2026-05-06_12Z.csv)")
        return

    print(f"Processing {len(files)} sounding file(s)...")
    for f in files:
        match = FILENAME_PATTERN.match(f.name)
        if not match:
            print(f"  Skipping (unexpected filename): {f.name}")
            continue

        date, hour_str = match.group(1), match.group(2)
        record = extract_surface(f, date, int(hour_str))
        if record:
            records.append(record)
            print(f"  ✓ {f.name}  →  {record['temp_c']}°C  RH {record['rel_humidity_pct']}%")

    if not records:
        print("No valid records extracted.")
        return

    df = pd.DataFrame(records).sort_values("datetime").reset_index(drop=True)

    # Derived: daily mean temperature (average of 00Z and 12Z)
    df["date"] = pd.to_datetime(df["date"])
    daily = (
        df.groupby("date")
        .agg(
            temp_mean_c=("temp_c", "mean"),
            temp_max_c=("temp_c", "max"),
            temp_min_c=("temp_c", "min"),
            rh_mean_pct=("rel_humidity_pct", "mean"),
            wind_mean_m_s=("wind_speed_m_s", "mean"),
            n_soundings=("temp_c", "count"),
        )
        .reset_index()
    )

    # Heating and Cooling Degree Days (base 15.5°C / 18°C — Hungarian standard)
    BASE_HEAT = 15.5
    BASE_COOL = 18.0
    daily["HDD"] = (BASE_HEAT - daily["temp_mean_c"]).clip(lower=0)
    daily["CDD"] = (daily["temp_mean_c"] - BASE_COOL).clip(lower=0)

    df.to_csv(OUT_FILE.parent / "soundings_raw_surface.csv", index=False)
    daily.to_csv(OUT_FILE, index=False)

    print(f"\nDone.")
    print(f"  Raw surface records : {OUT_FILE.parent}/soundings_raw_surface.csv  ({len(df)} rows)")
    print(f"  Daily aggregated    : {OUT_FILE}  ({len(daily)} days)")
    print(f"\nSample:")
    print(daily.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()

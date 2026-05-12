"""
fetch_entso_e.py
----------------
Downloads Hungarian electricity load and transmission loss data
from the ENTSO-E Transparency Platform using the entsoe-py client.

Requires:
  - ENTSO_E_API_KEY set in .env
  - pip install entsoe-py python-dotenv

Output:
  data/raw/entso_e/entso_e_load_HU_YYYY.csv      — hourly actual load (MW)
  data/raw/entso_e/entso_e_losses_HU_YYYY.csv    — transmission losses where available

Hungary bidding zone code: 10YHU-MAVIR----U
"""

import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from entsoe import EntsoePandasClient
from dotenv import load_dotenv

load_dotenv()

OUT_DIR = Path("data/raw/entso_e")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HU_ZONE = "10YHU-MAVIR----U"
START_YEAR = 2015
END_YEAR = 2024


def fetch_load(client: EntsoePandasClient, year: int) -> pd.Series | None:
    out_file = OUT_DIR / f"entso_e_load_HU_{year}.csv"
    if out_file.exists():
        print(f"  Already exists: {out_file.name}, skipping.")
        return None

    start = pd.Timestamp(f"{year}-01-01", tz="Europe/Budapest")
    end   = pd.Timestamp(f"{year}-12-31 23:59", tz="Europe/Budapest")

    print(f"  Fetching load {year}...")
    try:
        series = client.query_load(HU_ZONE, start=start, end=end)
        df = series.reset_index()
        df.columns = ["timestamp", "load_MW"]
        df.to_csv(out_file, index=False)
        print(f"  ✓ {out_file.name}  ({len(df)} hourly records)")
        return series
    except Exception as e:
        print(f"  ✗ Failed for {year}: {e}")
        return None


def fetch_crossborder(client: EntsoePandasClient, year: int):
    """
    Fetch cross-border flows to estimate transmission losses.
    Loss proxy = generation - load (where generation data is available).
    """
    out_file = OUT_DIR / f"entso_e_generation_HU_{year}.csv"
    if out_file.exists():
        print(f"  Already exists: {out_file.name}, skipping.")
        return

    start = pd.Timestamp(f"{year}-01-01", tz="Europe/Budapest")
    end   = pd.Timestamp(f"{year}-12-31 23:59", tz="Europe/Budapest")

    print(f"  Fetching generation mix {year}...")
    try:
        df = client.query_generation(HU_ZONE, start=start, end=end)
        df.to_csv(out_file)
        print(f"  ✓ {out_file.name}")
    except Exception as e:
        print(f"  ✗ Failed for {year}: {e}")


def main():
    api_key = os.getenv("ENTSO_E_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("ERROR: Set ENTSO_E_API_KEY in your .env file.")
        print("Request a key at: https://transparency.entsoe.eu")
        print("(My Account > Security Token — takes up to 24h)")
        return

    client = EntsoePandasClient(api_key=api_key)

    print(f"Fetching ENTSO-E data for Hungary ({START_YEAR}–{END_YEAR})")
    print(f"Bidding zone: {HU_ZONE}")
    print()

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Year {year}:")
        fetch_load(client, year)
        fetch_crossborder(client, year)
        print()

    print(f"Done. Files saved to {OUT_DIR}/")
    print("Next: run src/pipeline/merge_datasets.py")


if __name__ == "__main__":
    main()

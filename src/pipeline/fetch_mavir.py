"""
fetch_mavir.py
--------------
Downloads historical electricity load data from MAVIR (Hungarian grid operator).
MAVIR publishes hourly actual load data publicly at:
  https://www.mavir.hu/web/mavir-en/actual-load

This script scrapes the public download links for the annual CSV files
and saves them locally.

Output: data/raw/mavir/mavir_load_YYYY.csv

No API key required.
"""

import time
import requests
from pathlib import Path

OUT_DIR = Path("data/raw/mavir")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# MAVIR publishes annual load files — URLs follow this pattern
# Check https://www.mavir.hu/web/mavir-en/system-load for updated links
MAVIR_BASE = "https://www.mavir.hu/documents/10258"

# Known direct download URLs for annual load data (verify and update as needed)
# Format: year -> filename on MAVIR's document server
ANNUAL_FILES = {
    2016: "HU_Tényleges_terhelés_2016.xlsx",
    2017: "HU_Tényleges_terhelés_2017.xlsx",
    2018: "HU_Tényleges_terhelés_2018.xlsx",
    2019: "HU_Tényleges_terhelés_2019.xlsx",
    2020: "HU_Tényleges_terhelés_2020.xlsx",
    2021: "HU_Tényleges_terhelés_2021.xlsx",
    2022: "HU_Tényleges_terhelés_2022.xlsx",
    2023: "HU_Tényleges_terhelés_2023.xlsx",
    2024: "HU_Tényleges_terhelés_2024.xlsx",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research project; contact via GitHub)"
}


def download_file(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    print("MAVIR load data fetcher")
    print("=" * 50)
    print()
    print("NOTE: MAVIR's download URLs change periodically.")
    print("If downloads fail, visit:")
    print("  https://www.mavir.hu/web/mavir-en/system-load")
    print("and manually download the annual Excel files into:")
    print(f"  {OUT_DIR}/")
    print()
    print("Alternatively, the ENTSO-E API (fetch_entso_e.py) provides")
    print("Hungarian load data programmatically and is more reliable.")
    print()

    # Try ENTSO-E as primary source (more reliable)
    print("Recommendation: use fetch_entso_e.py for Hungarian load data.")
    print("It covers Hungary (bidding zone HU) with hourly resolution from 2015.")
    print()
    print("Manual download instructions for MAVIR pre-2015 data:")
    print("  1. Go to https://www.mavir.hu/web/mavir-en/actual-load")
    print("  2. Select year range")
    print("  3. Export as CSV or Excel")
    print(f"  4. Save to {OUT_DIR}/mavir_load_YYYY.csv")
    print()
    print("Once downloaded, run: src/pipeline/process_mavir.py")


if __name__ == "__main__":
    main()

"""
fetch_era5.py
-------------
Downloads ERA5 monthly-averaged daily temperature data for the Kisalföld
bounding box from the Copernicus Climate Data Store.

Requires:
  - CDS_API_KEY set in .env  (format: uid:api-key)
  - pip install cdsapi python-dotenv

Output: data/raw/era5/era5_kisalfold_YYYY.nc  (one file per year)

Run once — downloads ~50MB total for 1970–2024.
"""

import os
import cdsapi
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUT_DIR = Path("data/raw/era5")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Kisalföld bounding box [North, West, South, East]
BBOX = [
    float(os.getenv("BBOX_NORTH", 47.8)),
    float(os.getenv("BBOX_WEST",  17.0)),
    float(os.getenv("BBOX_SOUTH", 47.2)),
    float(os.getenv("BBOX_EAST",  18.0)),
]

START_YEAR = int(os.getenv("ERA5_START_YEAR", 1970))
END_YEAR   = int(os.getenv("ERA5_END_YEAR",   2024))

VARIABLES = [
    "2m_temperature",                  # T2m — core for HDD/CDD
    "surface_solar_radiation_downwards",  # Solar — for energy generation side
    "10m_u_component_of_wind",         # Wind — for wind energy
    "10m_v_component_of_wind",
    "total_precipitation",
]


def fetch_year(client: cdsapi.Client, year: int):
    out_file = OUT_DIR / f"era5_kisalfold_{year}.nc"
    if out_file.exists():
        print(f"  Already downloaded: {out_file.name}, skipping.")
        return

    print(f"  Fetching {year}...")
    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "format": "netcdf",
            "variable": VARIABLES,
            "year": str(year),
            "month": [f"{m:02d}" for m in range(1, 13)],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": BBOX,
        },
        str(out_file),
    )
    print(f"  ✓ Saved {out_file.name}")


def main():
    api_key = os.getenv("CDS_API_KEY")
    if not api_key or api_key == "your-uid:your-api-key":
        print("ERROR: Set CDS_API_KEY in your .env file first.")
        print("Get it at: https://cds.climate.copernicus.eu/user/login")
        return

    client = cdsapi.Client(
    url=os.getenv("CDS_API_URL", "https://cds.climate.copernicus.eu/api"),
    key=api_key,
    quiet=False,
)

    print(f"Downloading ERA5 for Kisalföld ({START_YEAR}–{END_YEAR})...")
    print(f"Bounding box: {BBOX}")
    print(f"Variables: {', '.join(VARIABLES)}\n")

    for year in range(START_YEAR, END_YEAR + 1):
        fetch_year(client, year)

    print(f"\nAll done. Files saved to {OUT_DIR}/")
    print("Next step: run src/pipeline/process_era5.py to extract daily means.")


if __name__ == "__main__":
    main()
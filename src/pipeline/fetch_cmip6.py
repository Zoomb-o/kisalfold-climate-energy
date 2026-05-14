"""
fetch_cmip6.py
--------------
Downloads CMIP6 temperature projections for the Kisalfold region
from the Copernicus Climate Data Store under three SSP scenarios.

Scenarios:
  SSP1-2.6  ~1.5C warming by 2100
  SSP2-4.5  ~2C warming by 2100  
  SSP5-8.5  ~3C warming by 2100

Output: data/raw/cmip6/cmip6_{scenario}.zip
"""

import os
import cdsapi
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUT_DIR = Path("data/raw/cmip6")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BBOX = [47.8, 17.0, 47.2, 18.0]  # North, West, South, East

SCENARIOS = {
    "ssp126": "ssp1_2_6",
    "ssp245": "ssp2_4_5",
    "ssp585": "ssp5_8_5",
}


def main():
    api_key = os.getenv("CDS_API_KEY")
    client = cdsapi.Client(
        url=os.getenv("CDS_API_URL", "https://cds.climate.copernicus.eu/api"),
        key=api_key,
        quiet=False,
    )

    for scenario_short, scenario_full in SCENARIOS.items():
        out_file = OUT_DIR / f"cmip6_{scenario_short}.zip"
        if out_file.exists():
            print(f"Already have {scenario_short}, skipping.")
            continue

        print(f"\nFetching {scenario_short} ({scenario_full})...")
        client.retrieve(
    "projections-cmip6",
    {
        "download_format": "zip",
        "data_format": "netcdf_legacy",
        "temporal_resolution": "monthly",
        "experiment": scenario_full,
        "level": "single_levels",
        "variable": "near_surface_air_temperature",
        "model": "mpi_esm1_2_hr",
        "date": "2015-01-01/2100-12-31",
        "area": BBOX,
    },
    str(out_file),
)
        print(f"Saved: {out_file}")

    print("\nAll done! Run src/pipeline/process_cmip6.py next.")


if __name__ == "__main__":
    main()
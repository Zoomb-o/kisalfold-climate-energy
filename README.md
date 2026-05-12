# Kisalföld Climate–Energy Study

**Climate-Driven Energy Demand Shifts in the Kisalföld Region: Historical Correlations, Future Projections, and Infrastructure Loss Implications**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![arXiv](https://img.shields.io/badge/arXiv-preprint-red.svg)](#)

A reproducible research project investigating how climate change affects energy consumption in the Kisalföld region of Hungary, combining local atmospheric sounding data with historical grid records and CMIP6 climate projections.

---

## Research Questions

1. How has rising temperature in Kisalföld correlated with regional energy consumption over the past 30–50 years?
2. Under CMIP6 warming scenarios (1.5 °C / 2 °C / 3 °C), how will energy demand shift by 2050?
3. How much of the projected surplus energy will be lost due to grid transmission inefficiencies and ageing infrastructure?

---

## Repository Structure

```
kisalfold-climate-energy/
├── data/
│   ├── raw/
│   │   ├── soundings/      # Local atmospheric sounding CSVs (2×daily)
│   │   ├── omsz/           # Hungarian Meteorological Service surface data
│   │   ├── era5/           # Copernicus ERA5 reanalysis (temperature, radiation)
│   │   ├── mavir/          # Hungarian grid operator load data
│   │   ├── entso_e/        # European grid transmission loss data
│   │   └── cmip6/          # Climate model projections (1.5°C / 2°C / 3°C)
│   └── processed/          # Cleaned, merged, feature-engineered datasets
├── notebooks/              # Exploratory analysis and figures (Jupyter)
├── src/
│   ├── pipeline/           # Data ingestion and cleaning scripts
│   ├── models/             # ML training and evaluation
│   └── visualization/      # Chart and map generation
├── pwa/                    # Interactive results dashboard (React PWA)
├── paper/                  # LaTeX source for the arXiv submission
├── results/
│   ├── figures/            # Publication-quality figures
│   └── tables/             # Result tables (CSV + LaTeX)
└── docs/                   # Project notes and data source documentation
```

---

## Data Sources

| Dataset | Source | Coverage | Access |
|---|---|---|---|
| Local soundings | Personal collection | 2025–present | This repo |
| Surface climate | [OMSZ](https://www.met.hu) | 1970–present | Free |
| ERA5 reanalysis | [Copernicus CDS](https://cds.climate.copernicus.eu) | 1940–present | Free (API) |
| Grid load | [MAVIR](https://www.mavir.hu) | 2010–present | Free |
| Transmission losses | [ENTSO-E](https://transparency.entsoe.eu) | 2015–present | Free (API key) |
| Climate projections | [CMIP6](https://esgf-node.llnl.gov) | 2025–2100 | Free |

---

## Setup

```bash
git clone https://github.com/Zoomb-o/kisalfold-climate-energy.git
cd kisalfold-climate-energy
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

---

## Reproducing the Analysis

```bash
# 1. Fetch all raw data
python src/pipeline/fetch_era5.py
python src/pipeline/fetch_mavir.py
python src/pipeline/fetch_entso_e.py

# 2. Process and merge
python src/pipeline/process_soundings.py
python src/pipeline/merge_datasets.py

# 3. Train models
python src/models/train_demand_model.py
python src/models/project_scenarios.py

# 4. Generate figures
python src/visualization/generate_figures.py
```

---

## Interactive Dashboard

A PWA (Progressive Web App) presenting the results interactively is available at:
**[zoomb-o.github.io/kisalfold-climate-energy](https://zoomb-o.github.io/kisalfold-climate-energy)**

---

## Paper

The preprint is available on arXiv: *(link will be added upon submission)*

LaTeX source is in the `paper/` directory.

---

## License

Code: [MIT](LICENSE)
Data derived from public sources: see individual source licenses in `docs/`.

---

## Author

**Zoomb-o** — Pápa, Kisalföld, Hungary

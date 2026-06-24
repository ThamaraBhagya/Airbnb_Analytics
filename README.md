# Expernetic Data Engineering Intern Assignment

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytical%20Warehouse-4A90E2?logo=duckdb&logoColor=white)
![Power%20BI](https://img.shields.io/badge/Power%20BI-Dashboarding-F2C811?logo=powerbi&logoColor=black)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Wrangling-150458?logo=pandas&logoColor=white)

> End-to-end medallion data engineering pipeline for the Cape Town Inside Airbnb dataset — covering ingestion, cleaning, enrichment, a DuckDB analytical warehouse, exploratory analysis, statistical hypothesis testing, an LLM-powered data copilot, and a Power BI market intelligence dashboard.

---

## Executive Summary

This repository delivers a Bronze → Silver → Gold pipeline for the Cape Town Inside Airbnb dataset (single-city scope, prioritizing depth over breadth — see `docs/decision_log.md` for the full rationale), followed by warehouse modeling, exploratory data analysis, formal statistical testing, an AI-assisted data copilot, and a business-facing dashboard. The goal is a reproducible analytics stack that turns raw marketplace data into decision-ready insight on pricing, supply, demand, seasonality, and host behavior — with every assumption, limitation, and engineering trade-off explicitly documented rather than hidden in code.

**Start here if you're reviewing this submission**, in this order:
1. This README (you are here)
2. `docs/dataset_schema.md` — what the data is and what was assumed about it
3. `docs/data_quality_report.md` — what was found wrong with it and how it was handled
4. `docs/decision_log.md` — why every major engineering choice was made
5. The notebooks, in the order listed in [Section 8](#8-run-the-analytical-notebooks)
6. The dashboard and data copilot demo (see [Section 9](#9-review-the-dashboard-and-data-copilot))

---

## Repository Architecture

```text
AIRBNB_PROJECT/
├── dashboards/                 # Power BI market intelligence dashboard (.pbix + exported .pdf)
├── data/                       # Medallion layers and warehouse artifacts
│   ├── bronze/                 # Raw source files: CSV and GeoJSON inputs, untouched
│   ├── silver/                 # Cleaned, validated, type-cast Parquet outputs
│   ├── gold/                   # Joined, enriched, business-ready Parquet tables
│   └── warehouse/              # DuckDB analytical warehouse (airbnb.duckdb)
├── docs/                       # Schema, data quality, decision log, and architecture docs
│   ├── dataset_schema.md           # Column-level schema, relationships, business context
│   ├── data_quality_report.md      # Missingness, outliers, duplicates, validation results
│   ├── data_dictionary.md          # Gold-layer column definitions and caveats
│   ├── decision_log.md             # Engineering trade-offs: what, why, what was given up
│   └── pipeline_architecture.md    # Section 3.5/3.6 design: incremental processing, CDC, scaling
├── notebooks/
│   ├── 01_data_profiling.ipynb              # Profiling, referential integrity, outlier investigation
│   ├── eda/
│   │   ├── 01_summary_statistics_distributions.ipynb
│   │   ├── 02_geographic_spatial_analysis.ipynb
│   │   ├── 03_temporal_seasonal_trends.ipynb
│   │   └── 04_host_supply_review_demand.ipynb
│   └── 05_statistical_analysis.ipynb        # Hypothesis testing, OLS regression, VIF, LOWESS
├── reports/
│   └── figures/                 # Exported chart images referenced by the notebooks
├── sql/
│   └── analysis_queries.sql     # Reusable queries against the DuckDB warehouse
├── src/
│   ├── ingest.py                 # Bronze: repeatable download + extraction
│   ├── clean.py                  # Silver: cleaning, validation, standardization
│   ├── enrich.py                 # Gold: joins, aggregates, derived business fields
│   ├── build_warehouse.py         # DuckDB star schema build
│   └── pipeline.py                 # End-to-end orchestrator (logging + retry)
├── data-copilot/                     # LLM-powered data copilot (see Section 7 below)
├── pipeline.log                 # Execution log from the most recent pipeline run
├── requirements.txt
└── README.md
```

### What each layer does

| Layer | Responsibility |
|---|---|
| `data/bronze/` | Raw source material, exactly as downloaded — never modified |
| `src/ingest.py` | Downloads and extracts raw files into Bronze |
| `src/clean.py` | Type-casts, validates, deduplicates, flags outliers → writes Silver |
| `src/enrich.py` | Joins listings/calendar/reviews, computes derived metrics → writes Gold |
| `src/build_warehouse.py` | Materializes a star schema (`dim_listing`, `fact_calendar`, `dim_date`) in DuckDB |
| `notebooks/01_data_profiling.ipynb` | Documents the investigation behind every assumption in `docs/` |
| `notebooks/eda/` | Section 4 — distributions, geography, seasonality, host/demand analysis |
| `notebooks/05_statistical_analysis.ipynb` | Section 5 — hypothesis tests, regression, effect sizes |
| `data-copilot/` | Section 7 — natural-language Q&A interface over the Gold layer |
| `dashboards/` | Section 8 — business-facing Power BI market intelligence view |
| `docs/` | The audit trail: every assumption, limitation, and trade-off, in writing |

---

## Assignment Completion Map

| Assignment Section | What Was Delivered | Evidence in This Repository |
|---|---|---|
| 02 — Dataset Familiarization | Schema documentation, relationship mapping, assumptions, limitations | `docs/dataset_schema.md`, `notebooks/01_data_profiling.ipynb` |
| 03 — Data Engineering Challenges | Ingestion, cleaning, enrichment, star schema, pipeline orchestration | `src/`, `data/silver/`, `data/gold/`, `data/warehouse/`, `sql/analysis_queries.sql`, `docs/pipeline_architecture.md` |
| 04 — Exploratory Data Analysis | Distributions, geographic analysis, seasonality, host/demand analysis, business interpretation throughout | `notebooks/eda/` (4 notebooks) |
| 05 — Statistical Analysis | Hypothesis testing (H1–H4 tested, H5 documented as not testable), confidence intervals, effect sizes, OLS regression, VIF, LOWESS | `notebooks/05_statistical_analysis.ipynb` |
| 06 — Data Science Challenges | *Not attempted — deprioritized in favor of depth on Sections 02–05 and 07–08. See `docs/decision_log.md`.* | — |
| 07 — AI & LLM Opportunities | LLM-powered data copilot for natural-language queries over the dataset |  — *(This was create in a separate repository)* |
| 08 — Open Innovation Challenge | Power BI market intelligence dashboard: supply density & price heatmap | `dashboards/Cape Town Supply Density & Price Heatmap.pbix`, `.pdf` |

> **Note on scope:** Sections 02–05 were treated as the core, mandatory-depth deliverable. Section 06 (Data Science / ML) was deliberately not attempted within the available time budget, in line with the assignment's own stated philosophy that depth on fewer sections outperforms shallow coverage of all of them. This trade-off, and the reasoning behind it, is recorded in `docs/project_execution_summary.md` and in the report's "Summary: Incomplete Work" section.

---

## Reproducibility Guide

### 1) Prerequisites

- Python 3.10 or later
- `pip`
- Git
- Jupyter (for running the notebooks)
- Power BI Desktop (for opening the `.pbix` dashboard — Windows only; the exported `.pdf` is viewable on any platform)

### 2) Clone the repository

```bash
git clone https://github.com/ThamaraBhagya/Airbnb_Analytics.git

Uploading 0624.mp4…


cd airbnb_project
```

### 3) Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4) Install dependencies

```bash
pip install -r requirements.txt
```

This installs `pandas`, `numpy`, `duckdb`, `pyarrow`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, and Jupyter support. If you add the data copilot's dependencies separately (e.g. an LLM SDK), confirm they're also listed in `requirements.txt` or noted in `copilot/README.md` before submission.

### 5) Download and place the raw data

This project uses the Cape Town Inside Airbnb scrape dated **2025-09-28 / 2025-09-29**. Place the following files in `data/bronze/`:

- `listings.csv`
- `calendar.csv`
- `reviews.csv`
- `neighbourhoods.csv`
- `neighbourhoods.geojson`

If you are reviewing the committed snapshot rather than rebuilding from scratch, `data/bronze/` should already contain these files — confirm before re-running the pipeline, since `src/ingest.py` skips downloads for files that already exist.

### 6) Rebuild the pipeline

**Preferred — single command:**
```bash
python src/pipeline.py
```

**Manual, stage-by-stage** (useful for debugging a single stage):
```bash
python src/ingest.py
python src/clean.py
python src/enrich.py
python src/build_warehouse.py
```

Each run appends to `pipeline.log`, including row counts at each stage — check this file first if a stage fails.

### 7) Validate the rebuild

After the pipeline completes, confirm:

- [ ] `data/silver/` contains `listings_clean.parquet`, `calendar_clean.parquet`, `reviews_clean.parquet`
- [ ] `data/gold/` contains `listing_master.parquet`, `neighbourhood_aggregates.parquet`
- [ ] `data/warehouse/airbnb.duckdb` exists and opens without error
- [ ] `pipeline.log` ends with a success message, not a traceback

### 8) Run the analytical notebooks

Run in this order — later notebooks read from the Gold layer and assume earlier documentation has already established the relevant assumptions:

1. `notebooks/01_data_profiling.ipynb` — profiling, integrity checks, outlier investigation
2. `notebooks/eda/01_summary_statistics_distributions.ipynb`
3. `notebooks/eda/02_geographic_spatial_analysis.ipynb`
4. `notebooks/eda/03_temporal_seasonal_trends.ipynb`
5. `notebooks/eda/04_host_supply_review_demand.ipynb`
6. `notebooks/05_statistical_analysis.ipynb`

### 9) Review the dashboard and data copilot

**Dashboard:** Open `dashboards/Cape Town Supply Density & Price Heatmap.pbix` in Power BI Desktop, or view the exported `dashboards/Cape Town Supply Density & Price Heatmap.pdf` directly if Power BI isn't available. The dashboard connects to the Gold-layer Parquet outputs produced in Step 6.

**Data Copilot:**
- 🎥 **Demo video:** `[Insert link here if recorded]`
- 💻 **Project Repository:** [View Source Code on GitHub](https://github.com/ThamaraBhagya/Data-Copilot)

  
## AI Tools Usage Disclosure

| Disclosure Item | Details |
|---|---|
| AI tools used | *(list every tool and model version actually used — e.g. Claude Sonnet 4.6, ChatGPT, GitHub Copilot, etc.)* |
| AI-assisted sections | Code scaffolding for the ETL pipeline, notebook structure, and documentation drafting. All cleaning logic, statistical test selection, and engineering decisions were reviewed, verified against the actual data, and corrected where the AI's initial suggestions were wrong (see `docs/decision_log.md` for examples — e.g., the calendar price-null root-cause investigation, the price-outlier hypothesis test). |
| Prompts used | See Appendix A of the final PDF report for key prompts |
| Output validation | Every AI-suggested cleaning step was run against the actual dataset and cross-checked with profiling output before being kept; several initial AI hypotheses (e.g., price outliers being long-stay rates) were tested and rejected based on evidence |
| Modifications made | *(note any AI-generated code you substantially rewrote)* |
| Critical assessment | Documented inline in `docs/project_execution_summary.md` wherever an AI suggestion was investigated and overturned |

---

## Known Limitations

These are dataset-level constraints, not implementation gaps — full reasoning in `docs/data_quality_report.md`:

- **Calendar pricing is 100% null** in this scrape. Seasonal and weekend-vs-weekday price analysis (EDA Section 4.3, Hypothesis H5) is explicitly out of scope and documented as untestable, rather than approximated.
- **Revenue and occupancy estimates use static listing price**, not actual daily calendar price, and carry a documented upward bias (`is_revenue_estimate_approximate` flag in the Gold layer).
- **Single-city scope** (Cape Town only) — multi-city comparison methods (Section 5.4) are not applicable.
- **Section 06 (Data Science / ML challenges)** was not attempted, by deliberate prioritization decision.

---



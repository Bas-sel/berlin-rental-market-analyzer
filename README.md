# Berlin Rental Market Analyzer

<!-- Replace this line with a screenshot of your Power BI dashboard once Phase 5 is complete -->
<!-- ![Dashboard Preview](reports/figures/dashboard_preview.png) -->

![Python](https://img.shields.io/badge/Python-3.11.5-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.1.4-150458?logo=pandas&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

An end-to-end data analytics project exploring the Berlin residential rental market.
The project covers the full analytics workflow — data acquisition, cleaning,
SQL-based analysis, Python visualisations, and an interactive Power BI dashboard —
using a real-world Berlin housing dataset.

Built as a portfolio project targeting data analyst roles in the German job market,
with a deliberate focus on SQL and Power BI as core deliverables.

---

## Key Findings

> *(This section will be completed in Phase 6 once the full analysis is done.)*
> ------------------------------

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data wrangling | Python 3.11.5, Pandas, NumPy |
| Database | SQLite, SQLAlchemy |
| Visualisation | Matplotlib, Seaborn |
| BI Dashboard | Power BI Desktop, DAX |
| Version control | Git, GitHub |

---

## Project Structure

```
berlin-rental-market-analyzer/
│
├── data/
│   ├── raw/            # Original dataset — never modified (gitignored if > 50 MB)
│   └── clean/          # Cleaned data + SQL query outputs (CSV exports)
│
├── notebooks/          # Jupyter notebooks — EDA and analysis
│
├── src/                # Python scripts — cleaning pipeline, SQL loader, visualisations
│
├── sql/                # All .sql query files
│
├── reports/
│   └── figures/        # Chart outputs (PNG, 300 dpi)
│
├── powerbi/            # Power BI .pbix file + exported PDF
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run

```bash
# 1. Clone the repository
git clone https://github.com/Bas-sel/berlin-rental-market-analyzer.git
cd berlin-rental-market-analyzer

# 2. Create and activate the conda environment
conda create -n berlin_rental python=3.11.5
conda activate berlin_rental

# 3. Install dependencies
pip install -r requirements.txt

```

## Phases

| Phase | Description | Status |
|---|---|---|
| 0 | Setup & Foundation | ✅ Complete |
| 1 | Data Acquisition | ✅ Complete |
| 2 | Data Cleaning & EDA | ✅ Complete |
| 3 | SQLite Database & SQL Analysis | ✅ Complete |
| 4 | Python Visualisations | 🔲 Pending |
| 5 | Power BI Dashboard | 🔲 Pending |
| 6 | Polish, Documentation & Launch | 🔲 Pending |

---

## Data Source

**Dataset:** [Apartment Rental Offers in Germany](https://www.kaggle.com/datasets/corrieaar/apartment-rental-offers-in-germany)  
**Source:** ImmobilienScout24 scrapes via Kaggle (corrieaar)  
**Coverage:** Germany-wide, four scrape dates: Sep 2018 – Feb 2020  
**Berlin subset:** 10,406 listings after filtering `regio1 == 'Berlin'`  
**License:** CC BY-NC-SA 4.0 — non-commercial use  

> The raw CSV is not committed to this repo. To download it, set up your Kaggle API
> credentials (see [Kaggle API docs](https://www.kaggle.com/docs/api)), then run:
> ```
> python src/download_data.py
> ```

---

## License

This project is licensed under the MIT License.

---

*Built by Bassel Kurbaj · https://www.linkedin.com/in/baselku*

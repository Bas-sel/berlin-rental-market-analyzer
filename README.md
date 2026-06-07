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
> Example placeholders:
> - Mitte and Prenzlauer Berg command the highest median rents per m²
> - Furnished listings carry a X% premium over unfurnished equivalents
> - Properties under 40 m² show the steepest price-per-sqm rates
> - Districts in the south-east offer the best affordability relative to size

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
git clone https://github.com/YOUR_USERNAME/berlin-rental-market-analyzer.git
cd berlin-rental-market-analyzer

# 2. Create and activate the conda environment
conda create -n berlin_rental python=3.11.5
conda activate berlin_rental

# 3. Install dependencies
pip install -r requirements.txt
```

> **Data:** Download the raw dataset from [Kaggle — link to be added] and place it in `data/raw/`.
> See Phase 1 notes for the exact download command.

---

## Phases

| Phase | Description | Status |
|---|---|---|
| 0 | Setup & Foundation | ✅ Complete |
| 1 | Data Acquisition | 🔲 Pending |
| 2 | Data Cleaning & EDA | 🔲 Pending |
| 3 | SQLite Database & SQL Analysis | 🔲 Pending |
| 4 | Python Visualisations | 🔲 Pending |
| 5 | Power BI Dashboard | 🔲 Pending |
| 6 | Polish, Documentation & Launch | 🔲 Pending |

---

## Data Source

> *(To be completed in Phase 1 once the dataset is confirmed.)*
> Dataset: [Dataset name] via Kaggle — [license type]

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Built by [Your Name] · [Your LinkedIn or GitHub profile link]*

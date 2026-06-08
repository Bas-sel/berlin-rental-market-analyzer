"""
Berlin Rental Market Analyzer — Phase 3
File: src/run_all_queries.py
Purpose: Executes all 10 analytical SQL queries against the SQLite database and
         exports each result as a CSV to data/clean/.

These CSVs are the direct input for the Phase 5 Power BI dashboard.

Usage (run from the project root directory):
    python src/run_all_queries.py

Output:
    data/clean/q01_avg_rent_by_bezirk.csv
    data/clean/q02_price_per_sqm_by_size.csv
    data/clean/q03_district_rent_rank.csv
    data/clean/q04_above_city_average.csv
    data/clean/q05_kitchen_premium.csv
    data/clean/q06_bezirk_rent_gap.csv
    data/clean/q07_affordability_cte.csv
    data/clean/q08_property_type_breakdown.csv
    data/clean/q09_high_volume_districts.csv
    data/clean/q10_amenity_impact.csv

Verification step (required by the mistake-free protocol):
    Every CSV listed above must be non-empty after this script finishes.
    The script prints row counts for each — review them before moving to Phase 4.
    Paste any error tracebacks to Claude rather than trying to fix them yourself.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH    = PROJECT_ROOT / "data" / "berlin_rentals.db"
SQL_DIR    = PROJECT_ROOT / "sql"
OUTPUT_DIR = PROJECT_ROOT / "data" / "clean"

# Ordered list of (sql_filename, output_csv_stem) pairs.
# Adding a new query is as simple as appending one line here.
QUERIES = [
    ("01_avg_rent_by_bezirk.sql",      "q01_avg_rent_by_bezirk"),
    ("02_price_per_sqm_by_size.sql",   "q02_price_per_sqm_by_size"),
    ("03_district_rent_rank.sql",      "q03_district_rent_rank"),
    ("04_above_city_average.sql",      "q04_above_city_average"),
    ("05_kitchen_premium.sql",         "q05_kitchen_premium"),
    ("06_bezirk_rent_gap.sql",         "q06_bezirk_rent_gap"),
    ("07_affordability_cte.sql",       "q07_affordability_cte"),
    ("08_property_type_breakdown.sql", "q08_property_type_breakdown"),
    ("09_high_volume_districts.sql",   "q09_high_volume_districts"),
    ("10_amenity_impact.sql",          "q10_amenity_impact"),
]

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# =============================================================================
# Core functions
# =============================================================================

def run_single_query(conn: sqlite3.Connection, sql_path: Path, output_path: Path) -> int:
    """
    Reads a SQL file, executes it against conn, and writes the result as a CSV.
    Returns the number of rows in the result.

    Raises an exception (caught by the caller) if the SQL fails — the caller
    will log the error and continue with the remaining queries.
    """
    sql = sql_path.read_text(encoding="utf-8")
    df  = pd.read_sql_query(sql, conn)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compat
    return len(df)


def print_summary_table(results: list, errors: list) -> None:
    """Prints a clean summary table of all query outcomes."""
    log.info("=" * 65)
    log.info("QUERY EXECUTION SUMMARY")
    log.info("=" * 65)
    log.info("%-50s %s", "Query file", "Rows")
    log.info("-" * 65)
    for sql_file, n_rows, csv_name in results:
        log.info("✓  %-47s %d", sql_file, n_rows)
    for sql_file in errors:
        log.info("✗  %-47s FAILED", sql_file)
    log.info("-" * 65)
    log.info(
        "Completed: %d / %d queries.  %s",
        len(results),
        len(QUERIES),
        "All succeeded." if not errors else f"{len(errors)} failed — see errors above.",
    )
    log.info("CSVs saved to: %s", OUTPUT_DIR)


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    log.info("=" * 65)
    log.info("Phase 3 — Running all analytical SQL queries")
    log.info("=" * 65)

    # Guard: database must exist before running queries
    if not DB_PATH.exists():
        log.error("Database not found: %s", DB_PATH)
        log.error("Run src/load_to_sqlite.py first, then come back here.")
        raise FileNotFoundError(DB_PATH)

    # Ensure the output directory exists (it should from Phase 2, but just in case)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    results = []
    errors  = []

    for sql_file, csv_stem in QUERIES:
        sql_path    = SQL_DIR    / sql_file
        output_path = OUTPUT_DIR / f"{csv_stem}.csv"

        # Warn and skip if the SQL file is missing (helps catch typos in the list)
        if not sql_path.exists():
            log.warning("SQL file not found — skipping: %s", sql_path)
            errors.append(sql_file)
            continue

        try:
            n_rows = run_single_query(conn, sql_path, output_path)
            log.info("✓  %-50s → %d rows", sql_file, n_rows)
            results.append((sql_file, n_rows, output_path.name))

        except Exception as exc:
            # Log the full error so you can paste it to Claude if needed
            log.error("✗  %-50s → ERROR", sql_file)
            log.error("    %s", exc)
            errors.append(sql_file)

    conn.close()

    print_summary_table(results, errors)

    # Exit with a non-zero code if any queries failed — useful for CI / scripting
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

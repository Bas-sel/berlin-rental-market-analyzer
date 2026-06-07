"""
Phase 1 — Data Quality Check
==============================
Profiles the raw dataset and produces a structured report covering:
shape, dtypes, null counts, numeric statistics, categorical cardinality,
and duplicate rows.

Run this immediately after downloading the raw data — before touching anything.

Usage
-----
    python src/data_quality_check.py data/raw/immo_data.csv

Output
------
    Prints the full report to the console.
    Copy and paste the entire output to Claude for review.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path


# ── CONFIG ─────────────────────────────────────────────────────────────────────
# Maximum unique values a column can have before we stop listing all of them
CARDINALITY_LIMIT = 25
# Number of sample rows to show at the end
SAMPLE_ROWS = 3
# ───────────────────────────────────────────────────────────────────────────────


def _header(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def check_file_exists(filepath: str) -> Path:
    """
    Validate that the given CSV file exists.
    Exits with a clear error if the path is wrong.
    """
    p = Path(filepath)
    if not p.exists():
        print(f"ERROR: File not found — {p.resolve()}")
        print("Check that the path is correct and that download_data.py ran successfully.")
        sys.exit(1)
    return p


def report_shape(df: pd.DataFrame) -> None:
    """Report the row and column count."""
    _header("SHAPE")
    print(f"  Rows    : {df.shape[0]:>10,}")
    print(f"  Columns : {df.shape[1]:>10,}")


def report_dtypes(df: pd.DataFrame) -> None:
    """List every column and its inferred dtype."""
    _header("COLUMN DATA TYPES")
    print(f"  {'Column':<45} {'dtype'}")
    print(f"  {'-'*45} {'-'*15}")
    for col, dtype in df.dtypes.items():
        print(f"  {str(col):<45} {str(dtype)}")


def report_nulls(df: pd.DataFrame) -> None:
    """Show null counts and percentages, sorted worst-first."""
    _header("NULL COUNTS  (only columns with at least one null)")
    nulls = df.isnull().sum()
    null_pct = (nulls / len(df) * 100).round(2)
    null_df = (
        pd.DataFrame({"null_count": nulls, "null_%": null_pct})
        .loc[nulls > 0]
        .sort_values("null_%", ascending=False)
    )

    if null_df.empty:
        print("  No nulls detected.")
    else:
        print(f"  {'Column':<45} {'Null Count':>12} {'Null %':>10}")
        print(f"  {'-'*45} {'-'*12} {'-'*10}")
        for col, row in null_df.iterrows():
            print(f"  {str(col):<45} {int(row['null_count']):>12,} {row['null_%']:>9.1f}%")


def report_numeric_stats(df: pd.DataFrame) -> None:
    """Descriptive statistics for all numeric columns."""
    _header("NUMERIC COLUMNS — DESCRIPTIVE STATS")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        print("  No numeric columns found.")
        return

    stats = df[numeric_cols].describe().round(2)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print(stats.to_string())


def report_categoricals(df: pd.DataFrame) -> None:
    """
    For each object/category column, show:
    - unique value count and null count
    - value distribution (top 10) if under CARDINALITY_LIMIT distinct values
    - top 5 only if high cardinality
    """
    _header("CATEGORICAL COLUMNS — CARDINALITY & VALUE DISTRIBUTIONS")
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not cat_cols:
        print("  No categorical columns found.")
        return

    for col in cat_cols:
        n_unique = df[col].nunique()
        n_null = df[col].isnull().sum()
        print(f"\n  {col}  |  {n_unique} unique  |  {n_null:,} nulls")

        top_n = 10 if n_unique <= CARDINALITY_LIMIT else 5
        label = "(all values)" if n_unique <= CARDINALITY_LIMIT else f"(top {top_n} of {n_unique})"
        print(f"  {label}")

        val_counts = df[col].value_counts(dropna=False).head(top_n)
        for val, count in val_counts.items():
            pct = count / len(df) * 100
            display_val = str(val) if pd.notna(val) else "<null>"
            print(f"    {display_val:<40} {count:>8,}  ({pct:>5.1f}%)")


def report_duplicates(df: pd.DataFrame) -> None:
    """Count fully duplicate rows."""
    _header("DUPLICATE ROWS")
    n_dupes = df.duplicated().sum()
    pct = n_dupes / len(df) * 100
    status = "⚠  INVESTIGATE" if n_dupes > 0 else "✓  None found"
    print(f"  Duplicate rows : {n_dupes:,}  ({pct:.2f}%)  —  {status}")


def report_berlin_coverage(df: pd.DataFrame) -> None:
    """
    Check whether a 'regio1' or region column exists and report
    how many Berlin rows are present. This is Phase 1 specific.
    """
    _header("BERLIN COVERAGE CHECK")

    # Look for the most likely region column
    region_candidates = [c for c in df.columns if "regio" in c.lower() or "region" in c.lower()]

    if not region_candidates:
        print("  No region column found — cannot check Berlin coverage.")
        print("  Note: You will need to identify which column contains Berlin district info.")
        return

    col = region_candidates[0]
    print(f"  Using column: '{col}'")
    print()

    # Check for Berlin entries (case-insensitive)
    berlin_mask = df[col].str.contains("Berlin", case=False, na=False)
    n_berlin = berlin_mask.sum()
    pct_berlin = n_berlin / len(df) * 100

    print(f"  Total rows          : {len(df):>10,}")
    print(f"  Rows matching Berlin: {n_berlin:>10,}  ({pct_berlin:.1f}%)")

    if n_berlin == 0:
        print()
        print("  WARNING: Zero Berlin rows found in this column.")
        print("  Check the other region columns or column names below:")
        for c in region_candidates:
            print(f"    {c}: sample values → {df[c].dropna().unique()[:5].tolist()}")
    else:
        print()
        print("  ✓ Berlin rows confirmed. This is your working dataset after Phase 2 filter.")


def report_sample(df: pd.DataFrame) -> None:
    """Show the first few rows transposed for readability."""
    _header(f"SAMPLE — FIRST {SAMPLE_ROWS} ROWS (transposed)")
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", 60)
    print(df.head(SAMPLE_ROWS).T.to_string())


def run_quality_check(filepath: str) -> None:
    """
    Master function — runs the full quality check pipeline.
    Load, report, and summarise. Paste all output to Claude.
    """
    p = check_file_exists(filepath)

    print()
    print("=" * 65)
    print("  DATA QUALITY REPORT")
    print(f"  File: {p.name}")
    print("=" * 65)
    print("Paste this entire output to Claude before moving to Phase 2.")

    # low_memory=False prevents dtype warnings on mixed-type columns
    df = pd.read_csv(p, low_memory=False)

    report_shape(df)
    report_dtypes(df)
    report_nulls(df)
    report_numeric_stats(df)
    report_categoricals(df)
    report_duplicates(df)
    report_berlin_coverage(df)
    report_sample(df)

    print()
    print("=" * 65)
    print("  REPORT COMPLETE — paste full output to Claude for review.")
    print("=" * 65)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python src/data_quality_check.py <path_to_csv>")
        print("Example: python src/data_quality_check.py data/raw/immo_data.csv")
        sys.exit(1)

    run_quality_check(sys.argv[1])

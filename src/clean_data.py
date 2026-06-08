"""
clean_data.py
Phase 2 — Data Cleaning Pipeline
Berlin Rental Market Analyzer
──────────────────────────────────────────────────────────────────────────────
What this script does, in order:

  Step 1  Load the raw ImmobilienScout24 dataset (Germany-wide, ~268k rows)
  Step 2  Filter down to Berlin-only listings
  Step 3  Deduplicate: keep the most recent snapshot per listing ID
  Step 4  Drop columns that have no analytical value
  Step 5  Remove rows with placeholder / physically impossible values
  Step 6  Drop rows with nulls in the four critical columns
  Step 7  Standardise sub-district names (regio3) to the 12 official Bezirke
  Step 8  Engineer four derived columns
  Step 9  Run sanity-check assertions — ALL must pass before Phase 3 begins
  Step 10 Save the clean dataset to data/clean/berlin_listings_clean.csv

Run from the project root directory:
    python src/clean_data.py

If you get a UnicodeDecodeError when loading the file, change the encoding
argument in load_raw_data() from "utf-8" to "latin-1".
──────────────────────────────────────────────────────────────────────────────
"""

import os
import sys

import numpy  as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
#
# All file paths and numeric thresholds live here in one place.
# If you ever need to adjust a threshold, this is the only section you touch.
# ──────────────────────────────────────────────────────────────────────────────

RAW_FILE   = "data/raw/immo_data.csv"
CLEAN_FILE = "data/clean/berlin_listings_clean.csv"

# Outlier / placeholder thresholds — taken directly from the data dictionary.
# Values outside these ranges are data-entry errors, not real listings.
RENT_MIN    = 100
RENT_MAX    = 10_000
SPACE_MIN   = 10
SPACE_MAX   = 500
ROOMS_MAX   = 20
YEAR_MIN    = 1850
YEAR_MAX    = 2024
SERVICE_MAX = 2_000
FLOOR_MAX   = 50

# Scrape-date priority for deduplication.
# The same listing (scoutId) can appear in up to four snapshots.
# Lower number = more recent = the row we want to keep.
DATE_PRIORITY = {
    "Feb20": 1,   # most recent — keep this one when available
    "Oct19": 2,
    "May19": 3,
    "Sep18": 4,   # oldest — only kept if no later snapshot exists
}

# Columns confirmed as redundant, low-value, or free-text in the data
# dictionary (Groups E, F, G) plus the encoding-broken duplicate of streetPlain.
# The rationale for each group is documented in DATA_DICTIONARY.md.
COLUMNS_TO_DROP = [

    # Group E — redundant geography (exact duplicates of other columns)
    "geo_bln",
    "geo_krs",
    "yearConstructedRange",
    "baseRentRange",
    "livingSpaceRange",
    "noRoomsRange",

    # Group F — low-value / promotional / near-constant fields
    "telekomHybridUploadSpeed",
    "electricityKwhPrice",
    "electricityBasePrice",
    "energyEfficiencyClass",
    "heatingCosts",
    "noParkSpaces",
    "thermalChar",
    "telekomTvOffer",
    "telekomUploadSpeed",
    "picturecount",

    # Group G — free-text German listing descriptions
    "description",
    "facilities",

    # streetPlain is the clean UTF-8 version; street has HTML-encoded characters
    "street",
]

# Maps Berlin's 23 pre-2001 Bezirke to today's 12 official Bezirke.
#
# The regio3 column uses the format  Kiez_OldBezirk  (underscores for spaces).
# For example: "Lichterfelde_Steglitz" or "Prenzlauer_Berg_Prenzlauer_Berg".
# The old Bezirk is always the suffix — we extract it and map it here.
# Berlin merged its 23 Bezirke into 12 in 2001; the platform still uses the old names.
OLD_TO_NEW_BEZIRK = {
    # Pre-2001 Bezirk          → Current Bezirk
    "Mitte":                   "Mitte",
    "Tiergarten":              "Mitte",
    "Wedding":                 "Mitte",

    "Prenzlauer Berg":         "Pankow",
    "Weißensee":               "Pankow",
    "Pankow":                  "Pankow",

    "Hohenschönhausen":        "Lichtenberg",
    "Lichtenberg":             "Lichtenberg",

    "Friedrichshain":          "Friedrichshain-Kreuzberg",
    "Kreuzberg":               "Friedrichshain-Kreuzberg",

    "Treptow":                 "Treptow-Köpenick",
    "Köpenick":                "Treptow-Köpenick",

    "Neukölln":                "Neukölln",

    "Tempelhof":               "Tempelhof-Schöneberg",
    "Schöneberg":              "Tempelhof-Schöneberg",

    "Steglitz":                "Steglitz-Zehlendorf",
    "Zehlendorf":              "Steglitz-Zehlendorf",

    "Charlottenburg":          "Charlottenburg-Wilmersdorf",
    "Wilmersdorf":             "Charlottenburg-Wilmersdorf",

    "Spandau":                 "Spandau",
    "Reinickendorf":           "Reinickendorf",
    "Marzahn":                 "Marzahn-Hellersdorf",
    "Hellersdorf":             "Marzahn-Hellersdorf",
}

# Maps each Bezirk to a three-level price tier based on Berlin's rental market.
# This will be validated against actual data in the EDA notebook.
DISTRICT_TIER_MAP = {
    "Mitte":                        "Premium",
    "Charlottenburg-Wilmersdorf":   "Premium",
    "Friedrichshain-Kreuzberg":     "Premium",
    "Pankow":                       "Premium",    # Prenzlauer Berg pulls this tier up
    "Steglitz-Zehlendorf":          "Mid",
    "Tempelhof-Schöneberg":         "Mid",
    "Neukölln":                     "Mid",
    "Treptow-Köpenick":             "Mid",
    "Lichtenberg":                  "Mid",
    "Spandau":                      "Affordable",
    "Marzahn-Hellersdorf":          "Affordable",
    "Reinickendorf":                "Affordable",
}


# ──────────────────────────────────────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────────────────────────────────────

def log_step(step_number: int, description: str) -> None:
    """
    Prints a clearly visible separator before each pipeline step.
    Makes the console output easy to read when the script is running.
    """
    print(f"\n{'─' * 62}")
    print(f"  Step {step_number} — {description}")
    print(f"{'─' * 62}")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load raw data
# ──────────────────────────────────────────────────────────────────────────────

def load_raw_data(filepath: str) -> pd.DataFrame:
    """
    Loads the raw ImmobilienScout24 CSV from disk without modifying anything.

    low_memory=False is required because several columns contain mixed types
    (e.g. noRooms stores both integers and the placeholder 999.99), and pandas
    needs to read the full column before it can infer the correct dtype.
    """
    print(f"  Reading: {filepath}")

    df = pd.read_csv(filepath, low_memory=False, encoding="utf-8")

    print(f"  Loaded: {len(df):,} rows × {len(df.columns)} columns")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Filter to Berlin
# ──────────────────────────────────────────────────────────────────────────────

def filter_to_berlin(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keeps only listings where regio1 == 'Berlin'.

    The raw dataset is Germany-wide. Every analysis in this project is
    Berlin-specific, so all other states are discarded immediately.
    Expected result: ~10,406 rows (about 3.9% of the full dataset).
    """
    rows_before = len(df)

    df = df[df["regio1"] == "Berlin"].copy()

    rows_after = len(df)
    print(f"  Kept Berlin rows: {rows_before:,} → {rows_after:,} "
          f"(removed {rows_before - rows_after:,} non-Berlin rows)")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — Deduplicate listings
# ──────────────────────────────────────────────────────────────────────────────

def deduplicate_listings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes duplicate listings, keeping only the most recent snapshot.

    The dataset contains four scrape dates (Sep18, May19, Oct19, Feb20).
    The same listing (scoutId) can appear in multiple snapshots because the
    'date' column differs between them — so they are not exact duplicates.

    Strategy: assign a numeric priority to each date (Feb20 = 1, the one we
    want; Sep18 = 4, the oldest fallback), sort ascending so the most recent
    row comes first per scoutId, then drop duplicates keeping only the first.

    Why this matters: rent prices rose between 2018 and 2020. Keeping the
    most recent snapshot per listing gives us the most accurate rent values.
    """
    rows_before = len(df)

    # Attach a priority number to each row based on its scrape date
    df = df.copy()
    df["_date_priority"] = df["date"].map(DATE_PRIORITY)

    # Sort so that Feb20 (priority 1) always comes before older snapshots
    df = df.sort_values("_date_priority")

    # Keep the first occurrence of each scoutId — that is now the most recent
    df = df.drop_duplicates(subset="scoutId", keep="first")

    # The priority column was only needed for sorting; remove it now
    df = df.drop(columns=["_date_priority"])

    rows_after = len(df)
    print(f"  Deduplicated on scoutId: {rows_before:,} → {rows_after:,} "
          f"(removed {rows_before - rows_after:,} older duplicates)")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — Drop columns with no analytical value
# ──────────────────────────────────────────────────────────────────────────────

def drop_unneeded_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes columns confirmed as redundant, low-value, or free-text.

    The full rationale for each column is in DATA_DICTIONARY.md (Groups E, F,
    and G). We only drop columns that are actually present in this file —
    this prevents the script from crashing if the raw CSV has slightly
    different column names than documented.
    """
    # Split the drop list into present vs missing, so we can report both
    cols_to_drop  = [c for c in COLUMNS_TO_DROP if c     in df.columns]
    cols_missing  = [c for c in COLUMNS_TO_DROP if c not in df.columns]

    if cols_missing:
        print(f"  Note: {len(cols_missing)} expected columns were not found "
              f"and skipped: {cols_missing}")

    df = df.drop(columns=cols_to_drop)

    print(f"  Dropped {len(cols_to_drop)} columns. "
          f"Remaining: {len(df.columns)} columns")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Remove placeholder / outlier values
# ──────────────────────────────────────────────────────────────────────────────

def filter_placeholder_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows containing known placeholder or physically impossible values.

    ImmobilienScout24 uses sentinel values such as 0, 9,999,999, 999, and
    111,111 when a required field was left blank by the landlord. These are
    not real listings and will distort every analysis if left in.

    For columns that allow nulls (floor, serviceCharge, yearConstructed), we
    preserve NaN rows — only rows with out-of-range non-null values are dropped.

    Each filter is printed separately so you can see exactly how many rows
    each rule removes.
    """
    rows_before = len(df)
    print()

    # ── baseRent ────────────────────────────────────────────────────────────
    # Cold rent in EUR. Values outside 100–10,000 are placeholders or errors.
    mask    = df["baseRent"].between(RENT_MIN, RENT_MAX)
    removed = (~mask).sum()
    df      = df[mask].copy()
    print(f"  baseRent [{RENT_MIN}–{RENT_MAX} EUR]      : removed {removed:,} rows")

    # ── livingSpace ─────────────────────────────────────────────────────────
    # Floor area in m². Placeholder values include 0 and 111,111.
    mask    = df["livingSpace"].between(SPACE_MIN, SPACE_MAX)
    removed = (~mask).sum()
    df      = df[mask].copy()
    print(f"  livingSpace [{SPACE_MIN}–{SPACE_MAX} m²]   : removed {removed:,} rows")

    # ── noRooms ─────────────────────────────────────────────────────────────
    # Room count. Placeholder value is 999.99.
    mask    = df["noRooms"] <= ROOMS_MAX
    removed = (~mask).sum()
    df      = df[mask].copy()
    print(f"  noRooms [≤ {ROOMS_MAX}]               : removed {removed:,} rows")

    # ── yearConstructed ─────────────────────────────────────────────────────
    # Construction year. Contains values like 1000 and 2090. Nulls are kept.
    if "yearConstructed" in df.columns:
        mask    = df["yearConstructed"].isna() | df["yearConstructed"].between(YEAR_MIN, YEAR_MAX)
        removed = (~mask).sum()
        df      = df[mask].copy()
        print(f"  yearConstructed [{YEAR_MIN}–{YEAR_MAX}]  : removed {removed:,} rows")

    # ── serviceCharge ───────────────────────────────────────────────────────
    # Monthly operating costs. Values above 2,000 are data entry errors.
    # Nulls are kept — many listings simply did not fill in this field.
    if "serviceCharge" in df.columns:
        mask    = df["serviceCharge"].isna() | (df["serviceCharge"] <= SERVICE_MAX)
        removed = (~mask).sum()
        df      = df[mask].copy()
        print(f"  serviceCharge [≤ {SERVICE_MAX} EUR]    : removed {removed:,} rows")

    # ── floor ───────────────────────────────────────────────────────────────
    # Floor number. Placeholder is 999. Nulls are kept.
    if "floor" in df.columns:
        mask    = df["floor"].isna() | (df["floor"] <= FLOOR_MAX)
        removed = (~mask).sum()
        df      = df[mask].copy()
        print(f"  floor [≤ {FLOOR_MAX}]                : removed {removed:,} rows")

    # ── numberOfFloors ──────────────────────────────────────────────────────
    # Total floors in building. Same placeholder logic as floor.
    if "numberOfFloors" in df.columns:
        mask    = df["numberOfFloors"].isna() | (df["numberOfFloors"] <= FLOOR_MAX)
        removed = (~mask).sum()
        df      = df[mask].copy()
        print(f"  numberOfFloors [≤ {FLOOR_MAX}]       : removed {removed:,} rows")

    rows_after = len(df)
    print(f"\n  Total removed by placeholder filter: "
          f"{rows_before - rows_after:,} rows")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 — Drop rows with nulls in the four critical columns
# ──────────────────────────────────────────────────────────────────────────────

def drop_critical_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures the four columns that every analysis depends on contain no nulls.

    According to the data dictionary, baseRent, livingSpace, noRooms, and
    regio3 already have zero nulls in the raw file. This step is a safety
    net that verifies that assumption still holds after filtering.

    If rows are dropped here unexpectedly, the warning message will say so.
    Do not proceed to Phase 3 without understanding why rows were dropped.
    """
    critical_columns = ["baseRent", "livingSpace", "noRooms", "regio3"]
    rows_before      = len(df)

    df = df.dropna(subset=critical_columns)

    rows_dropped = rows_before - len(df)

    if rows_dropped == 0:
        print("  Critical-null check passed — no rows dropped (as expected)")
    else:
        print(f"  WARNING: {rows_dropped:,} rows dropped due to nulls in "
              f"critical columns.")
        print("  This is unexpected. Review your data before proceeding.")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 7 — Standardise Bezirk names
# ──────────────────────────────────────────────────────────────────────────────

def standardise_bezirk_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps the sub-district names in regio3 to Berlin's 12 official Bezirke.

    The regio3 column uses the format  Kiez_OldBezirk  with underscores
    replacing spaces. For example:
      "Lichterfelde_Steglitz"           → Steglitz → Steglitz-Zehlendorf
      "Prenzlauer_Berg_Prenzlauer_Berg" → Prenzlauer Berg → Pankow
      "Alt_Hohenschönhausen_Hohenschönhausen" → Hohenschönhausen → Lichtenberg

    The old Bezirk is always the suffix of the string. Berlin reorganised
    from 23 Bezirke to 12 in 2001; the platform still uses the pre-2001 names.
    The lookup extracts that suffix and maps it to the current Bezirk via
    OLD_TO_NEW_BEZIRK, trying a two-word suffix first (needed for
    "Prenzlauer Berg") and falling back to a single-word suffix.

    A new 'bezirk' column is added alongside the original regio3 so that
    the Kiez-level data is preserved for any granular analysis later.

    Any regio3 values not found in OLD_TO_NEW_BEZIRK are printed at the end.
    If you see unmapped values, paste them to Claude and they will be added.
    """

    def lookup_bezirk(raw_value) -> str:
        """
        Extracts the old Bezirk suffix from a regio3 value and maps it to
        the current Bezirk name.

        regio3 format: Kiez_OldBezirk  (underscores replace spaces)
        Examples:
          "Lichterfelde_Steglitz"           → suffix "Steglitz"  → "Steglitz-Zehlendorf"
          "Prenzlauer_Berg_Prenzlauer_Berg" → suffix "Prenzlauer Berg" → "Pankow"
          "Alt_Hohenschönhausen_Hohenschönhausen" → suffix "Hohenschönhausen" → "Lichtenberg"
        """
        if pd.isna(raw_value):
            return np.nan

        parts = str(raw_value).split("_")

        # Try a two-word suffix first.
        # "Prenzlauer Berg" is the only pre-2001 Bezirk with two words, but
        # checking two words first is harmless for all single-word cases.
        if len(parts) >= 2:
            two_word_suffix = parts[-2] + " " + parts[-1]
            if two_word_suffix in OLD_TO_NEW_BEZIRK:
                return OLD_TO_NEW_BEZIRK[two_word_suffix]

        # Fall back to the last token alone (covers all other 22 old Bezirke)
        one_word_suffix = parts[-1]
        return OLD_TO_NEW_BEZIRK.get(one_word_suffix, np.nan)

    df = df.copy()
    df["bezirk"] = df["regio3"].apply(lookup_bezirk)

    mapped   = df["bezirk"].notna().sum()
    unmapped = df["bezirk"].isna().sum()
    print(f"  Bezirk mapping: {mapped:,} rows mapped, {unmapped:,} unmapped")

    # Print unmapped values so they can be reviewed and added to BEZIRK_MAP
    if unmapped > 0:
        top_unmapped = (
            df.loc[df["bezirk"].isna(), "regio3"]
            .value_counts()
            .head(20)
        )
        print("\n  Top unmapped regio3 values (paste these to Claude to extend the map):")
        print(top_unmapped.to_string())

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 8 — Engineer derived features
# ──────────────────────────────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates four new columns defined in the data dictionary.

    price_per_sqm
        Cold rent (baseRent) divided by floor area (livingSpace).
        This is the primary normalised price metric for cross-district and
        cross-size comparisons. livingSpace was already filtered to ≥ 10,
        so division by zero is not possible.

    size_category
        livingSpace binned into four named categories:
          Micro  : < 40 m²    (studios, very small flats)
          Small  : 40–65 m²   (one to two rooms)
          Medium : 65–90 m²   (two to three rooms)
          Large  : > 90 m²    (family-sized flats)

    district_tier
        Each Bezirk assigned to a rental price tier (Premium / Mid /
        Affordable) based on Berlin's rental market. The tier boundaries
        are defined in DISTRICT_TIER_MAP and will be validated in the EDA.

    era
        yearConstructed grouped into four historically meaningful periods
        that are particularly relevant for Berlin because East and West
        building typologies align closely to these eras:
          Pre-1918   : Gründerzeit / Altbau
          1918–1945  : Weimar and WWII era
          1946–1990  : Post-war / GDR Plattenbau
          Post-1990  : Post-reunification / modern construction
    """
    df = df.copy()

    # ── price_per_sqm ───────────────────────────────────────────────────────
    df["price_per_sqm"] = (df["baseRent"] / df["livingSpace"]).round(2)

    # ── size_category ───────────────────────────────────────────────────────
    size_bins   = [0,   40,  65,  90,  float("inf")]
    size_labels = ["Micro", "Small", "Medium", "Large"]

    df["size_category"] = pd.cut(
        df["livingSpace"],
        bins   = size_bins,
        labels = size_labels,
        right  = False,   # intervals are [left, right): [0,40), [40,65), …
    )

    # ── district_tier ───────────────────────────────────────────────────────
    df["district_tier"] = df["bezirk"].map(DISTRICT_TIER_MAP)

    # ── era ─────────────────────────────────────────────────────────────────
    era_bins   = [0,    1918,      1945,      1990,      float("inf")]
    era_labels = ["Pre-1918", "1918–1945", "1946–1990", "Post-1990"]

    df["era"] = pd.cut(
        df["yearConstructed"],
        bins   = era_bins,
        labels = era_labels,
        right  = True,    # intervals are (left, right]: (0,1918], (1918,1945], …
    )

    # ── Distributions — printed so you can spot-check the values look right ─
    print("  Engineered columns added: price_per_sqm, size_category, "
          "district_tier, era\n")

    print("  size_category distribution:")
    print(df["size_category"].value_counts().to_string())

    print("\n  district_tier distribution:")
    print(df["district_tier"].value_counts().to_string())

    print("\n  era distribution:")
    print(df["era"].value_counts().to_string())

    print(f"\n  price_per_sqm — min: {df['price_per_sqm'].min():.2f}  "
          f"median: {df['price_per_sqm'].median():.2f}  "
          f"max: {df['price_per_sqm'].max():.2f}")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 9 — Sanity checks
# ──────────────────────────────────────────────────────────────────────────────

def run_sanity_checks(df: pd.DataFrame) -> None:
    """
    Runs assertions that must ALL pass before Phase 3 begins.

    Per the mistake-free protocol: verify values at every phase boundary.
    If any check fails the script stops immediately with a clear message.
    Fix the failing check before moving to Phase 3.
    """
    print()
    failures = []

    def check(condition: bool, label: str) -> None:
        """Records one pass or fail and prints the result."""
        symbol = "✓" if condition else "✗  FAILED"
        print(f"  {symbol}  {label}")
        if not condition:
            failures.append(label)

    # The cleaned Berlin dataset should land between 5,000 and 12,000 rows.
    # If it is below 5,000 something in the filtering was too aggressive.
    check(
        5_000 <= len(df) <= 12_000,
        f"Row count is plausible for Berlin: {len(df):,} rows"
    )

    # These four columns must have zero nulls — all downstream steps depend on them
    check(df["baseRent"].isna().sum()    == 0, "No nulls in baseRent")
    check(df["livingSpace"].isna().sum() == 0, "No nulls in livingSpace")
    check(df["noRooms"].isna().sum()     == 0, "No nulls in noRooms")
    check(df["regio3"].isna().sum()      == 0, "No nulls in regio3")

    # Every rent and area value must be within the thresholds we applied above
    check(
        df["baseRent"].between(RENT_MIN, RENT_MAX).all(),
        f"All baseRent values between {RENT_MIN} and {RENT_MAX} EUR"
    )
    check(
        df["livingSpace"].between(SPACE_MIN, SPACE_MAX).all(),
        f"All livingSpace values between {SPACE_MIN} and {SPACE_MAX} m²"
    )

    # price_per_sqm must be positive — confirmed by the space filter above,
    # but we check it explicitly because it is our primary analysis metric
    check(
        (df["price_per_sqm"] > 0).all(),
        "All price_per_sqm values are positive"
    )

    # At least 90% of rows should have a mapped Bezirk.
    # A lower value means the BEZIRK_MAP needs more entries.
    bezirk_coverage = df["bezirk"].notna().mean()
    check(
        bezirk_coverage >= 0.90,
        f"Bezirk mapping coverage ≥ 90%  (actual: {bezirk_coverage:.1%})"
    )

    # All rows must still be Berlin — the regio1 filter guaranteed this, but
    # it is cheap to verify and rules out any accidental data contamination
    check(
        (df["regio1"] == "Berlin").all(),
        "All rows have regio1 == 'Berlin'"
    )

    # There must be no remaining duplicate listing IDs
    check(
        df["scoutId"].duplicated().sum() == 0,
        "No duplicate scoutId values"
    )

    # ── Result ──────────────────────────────────────────────────────────────
    print()
    if failures:
        print(f"  {len(failures)} check(s) FAILED.")
        print(f"  Do not proceed to Phase 3 until these are resolved:")
        for f in failures:
            print(f"    • {f}")
        sys.exit(1)
    else:
        print("  All sanity checks passed. Ready to proceed to Phase 3.")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 10 — Save clean data
# ──────────────────────────────────────────────────────────────────────────────

def save_clean_data(df: pd.DataFrame, filepath: str) -> None:
    """
    Saves the cleaned DataFrame to CSV.

    Creates the output directory automatically if it does not exist yet
    (handles the case where data/clean/ has not been created manually).
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    df.to_csv(filepath, index=False, encoding="utf-8")

    print(f"\n  Saved: {filepath}")
    print(f"  Final shape: {len(df):,} rows × {len(df.columns)} columns")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN — runs all ten steps in sequence
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Executes the full cleaning pipeline from raw CSV to clean CSV.

    Every step prints its own output so you can follow what is happening
    and immediately see if something looks wrong.
    """
    print("=" * 62)
    print("  Berlin Rental Market Analyzer — Phase 2: Data Cleaning")
    print("=" * 62)

    log_step(1,  "Load raw data")
    df = load_raw_data(RAW_FILE)

    log_step(2,  "Filter to Berlin")
    df = filter_to_berlin(df)

    log_step(3,  "Deduplicate listings (keep most recent snapshot per ID)")
    df = deduplicate_listings(df)

    log_step(4,  "Drop columns with no analytical value")
    df = drop_unneeded_columns(df)

    log_step(5,  "Remove placeholder and outlier values")
    df = filter_placeholder_values(df)

    log_step(6,  "Drop rows with nulls in critical columns")
    df = drop_critical_nulls(df)

    log_step(7,  "Standardise Bezirk names (regio3 → bezirk)")
    df = standardise_bezirk_names(df)

    log_step(8,  "Engineer derived features")
    df = engineer_features(df)

    log_step(9,  "Run sanity checks")
    run_sanity_checks(df)

    log_step(10, "Save clean data")
    save_clean_data(df, CLEAN_FILE)

    print("\n" + "=" * 62)
    print("  Phase 2 complete.")
    print("=" * 62)


if __name__ == "__main__":
    main()

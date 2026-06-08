"""
Berlin Rental Market Analyzer — Phase 3
File: src/load_to_sqlite.py
Purpose: Reads the cleaned Berlin rental CSV produced by Phase 2 and loads it
         into the normalised SQLite database defined in sql/schema.sql.

Schema built
    dim_districts      — unique neighbourhood / Bezirk combinations
    dim_property_types — unique apartment type values
    fact_listings      — all listing rows with resolved FK references

Usage (run from the project root directory):
    python src/load_to_sqlite.py

Verification step (required by the mistake-free protocol):
    After this script finishes, open a SQLite browser or run:
        python -c "import sqlite3; c=sqlite3.connect('data/berlin_rentals.db'); print(c.execute('SELECT COUNT(*) FROM fact_listings').fetchone())"
    The number printed must match your cleaned CSV row count exactly.
"""

import logging
import sqlite3
import sys
from pathlib import Path

import pandas as pd

# =============================================================================
# Configuration — adjust paths here if your project layout differs
# =============================================================================

# Assumes you run this script from the project root (berlin-rental-market-analyzer/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLEAN_CSV  = PROJECT_ROOT / "data" / "clean" / "berlin_listings_clean.csv"
DB_PATH    = PROJECT_ROOT / "data" / "berlin_rentals.db"
SCHEMA_SQL = PROJECT_ROOT / "sql" / "schema.sql"

# =============================================================================
# Column map — left side: what Phase 2 may have called the column
#              right side: the internal name this script uses
#
# If your Phase 2 cleaning pipeline already renamed a column to its target name
# (e.g. base_rent instead of baseRent), this script will still find it — the
# resolution logic below checks both forms before warning you.
# =============================================================================

COLUMN_MAP = {
    # Identifiers
    "scoutId":         "scout_id",
    "date":            "scrape_date",

    # Geography
    "regio3":          "regio3",
    "bezirk":          "bezirk",          # derived in Phase 2 — mapped from regio3
    "district_tier":   "district_tier",   # derived in Phase 2

    # Property type
    "typeOfFlat":      "type_name",

    # Core financials
    "baseRent":        "base_rent",
    "livingSpace":     "living_space",
    "noRooms":         "no_rooms",
    "serviceCharge":   "service_charge",
    "totalRent":       "total_rent",

    # Physical
    "floor":           "floor_number",
    "yearConstructed": "year_constructed",
    "condition":       "condition_state",
    "interiorQual":    "interior_qual",
    "heatingType":     "heating_type",

    # Rental policy
    "petsAllowed":     "pets_allowed",

    # Amenity flags (will be converted to 0/1 integers)
    "hasKitchen":      "has_kitchen",
    "cellar":          "cellar",
    "balcony":         "balcony",
    "garden":          "garden",
    "lift":            "lift",
    "newlyConst":      "newly_const",

    # Geography
    "geo_plz":         "geo_plz",

    # Derived columns from Phase 2
    "price_per_sqm":   "price_per_sqm",
    "size_category":   "size_category",
    "era":             "era",
    "pricetrend":      "price_trend",
}

# Columns that are stored as 0/1 integers in SQLite (booleans)
BOOL_COLUMNS = {"has_kitchen", "cellar", "balcony", "garden", "lift", "newly_const"}

# Columns that belong in fact_listings (must match schema.sql exactly)
FACT_COLUMNS = [
    "scout_id", "scrape_date",
    "district_id", "property_type_id",
    "base_rent", "living_space", "no_rooms", "service_charge", "total_rent",
    "floor_number", "year_constructed", "condition_state", "interior_qual",
    "heating_type", "pets_allowed",
    "has_kitchen", "cellar", "balcony", "garden", "lift", "newly_const",
    "geo_plz",
    "price_per_sqm", "size_category", "era", "price_trend",
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
# Step 1 — Load the clean CSV
# =============================================================================

def load_clean_csv(path: Path) -> pd.DataFrame:
    """
    Reads the Phase 2 clean CSV and applies the COLUMN_MAP rename.

    Handles two cases gracefully:
      - Column still has its original Phase 2 name (e.g. 'baseRent')
      - Column was already renamed by Phase 2 to the target name (e.g. 'base_rent')

    Logs a warning (but does NOT crash) for any column that cannot be found
    under either name. Those columns will be absent from the database.
    """
    if not path.exists():
        log.error("Clean CSV not found: %s", path)
        log.error("Make sure Phase 2 has been completed and the file saved there.")
        sys.exit(1)

    log.info("Loading CSV: %s", path)
    df = pd.read_csv(path, low_memory=False)
    log.info("CSV shape: %d rows × %d columns", *df.shape)
    log.info("Columns in CSV: %s", df.columns.tolist())

    # Build a rename mapping using only columns that actually exist
    rename = {}
    for original, target in COLUMN_MAP.items():
        if original in df.columns:
            rename[original] = target          # column found under its original name
        elif target in df.columns:
            pass                               # already renamed by Phase 2 — keep as-is
        else:
            log.warning(
                "Column not found under either name — will be NULL in DB: "
                "original='%s', target='%s'",
                original, target,
            )

    if rename:
        df = df.rename(columns=rename)
        log.info("Renamed %d columns.", len(rename))

    return df


# =============================================================================
# Step 2 — Populate dim_districts
# =============================================================================

def build_dim_districts(df: pd.DataFrame, conn: sqlite3.Connection) -> dict:
    """
    Inserts one row per unique regio3 value into dim_districts.
    Returns a dict mapping   regio3 (str) → district_id (int)
    so that fact_listings rows can reference the correct FK.
    """
    required = {"regio3", "bezirk"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Cannot build dim_districts — required columns missing: {missing}.\n"
            "Check COLUMN_MAP or your Phase 2 output column names."
        )

    # Collect unique (regio3, bezirk, district_tier) combinations
    dim_cols = ["regio3", "bezirk"]
    if "district_tier" in df.columns:
        dim_cols.append("district_tier")

    districts = (
        df[dim_cols]
        .drop_duplicates(subset=["regio3"])
        .sort_values("regio3")
        .reset_index(drop=True)
    )

    # Insert row by row — INSERT OR IGNORE respects the unique index on regio3
    for _, row in districts.iterrows():
        tier = row.get("district_tier", None) if "district_tier" in districts.columns else None
        conn.execute(
            """
            INSERT OR IGNORE INTO dim_districts (regio3, bezirk, district_tier)
            VALUES (?, ?, ?)
            """,
            (row["regio3"], row["bezirk"], tier),
        )

    conn.commit()

    # Build the regio3 → district_id lookup dict
    cursor = conn.execute("SELECT regio3, district_id FROM dim_districts")
    mapping = {row[0]: row[1] for row in cursor.fetchall()}
    log.info("dim_districts  → %d rows inserted.", len(mapping))
    return mapping


# =============================================================================
# Step 3 — Populate dim_property_types
# =============================================================================

def build_dim_property_types(df: pd.DataFrame, conn: sqlite3.Connection) -> dict:
    """
    Inserts one row per unique typeOfFlat value into dim_property_types.
    Returns a dict mapping   type_name (str) → property_type_id (int).
    If the type_name column is missing from the CSV, returns an empty dict
    and logs a warning — fact_listings will have NULL for property_type_id.
    """
    if "type_name" not in df.columns:
        log.warning(
            "'typeOfFlat' / 'type_name' column not found — "
            "dim_property_types will be empty and property_type_id will be NULL."
        )
        return {}

    unique_types = sorted(df["type_name"].dropna().unique())

    for raw_name in unique_types:
        # Convert snake_case to Title Case for a readable display label
        label = raw_name.replace("_", " ").title()
        conn.execute(
            "INSERT OR IGNORE INTO dim_property_types (type_name, type_label) VALUES (?, ?)",
            (raw_name, label),
        )

    conn.commit()

    cursor = conn.execute("SELECT type_name, property_type_id FROM dim_property_types")
    mapping = {row[0]: row[1] for row in cursor.fetchall()}
    log.info("dim_property_types → %d rows inserted.", len(mapping))
    return mapping


# =============================================================================
# Step 4 — Populate fact_listings
# =============================================================================

def build_fact_listings(
    df: pd.DataFrame,
    conn: sqlite3.Connection,
    district_map: dict,
    property_type_map: dict,
) -> None:
    """
    Inserts all listing rows into fact_listings, replacing regio3 and type_name
    with their resolved FK integer IDs.
    """
    fact_df = df.copy()

    # --- Resolve foreign keys ------------------------------------------------
    fact_df["district_id"] = (
        fact_df["regio3"].map(district_map) if "regio3" in fact_df.columns else None
    )
    fact_df["property_type_id"] = (
        fact_df["type_name"].map(property_type_map) if "type_name" in fact_df.columns else None
    )

    # Warn if any FK could not be resolved (NaN means regio3 wasn't in dim_districts)
    unresolved_districts = fact_df["district_id"].isna().sum()
    if unresolved_districts > 0:
        log.warning("%d rows could not be matched to a district_id.", unresolved_districts)

    # --- Keep only the fact table columns ------------------------------------
    available = [col for col in FACT_COLUMNS if col in fact_df.columns]
    missing_fact_cols = [col for col in FACT_COLUMNS if col not in fact_df.columns]
    if missing_fact_cols:
        log.warning("Fact columns absent from CSV (stored as NULL): %s", missing_fact_cols)

    fact_df = fact_df[available].copy()

    # --- Convert boolean columns to 0 / 1 integers --------------------------
    for bool_col in BOOL_COLUMNS:
        if bool_col in fact_df.columns:
            # Handles both Python booleans and string 'True'/'False' values
            fact_df[bool_col] = (
                fact_df[bool_col]
                .map(lambda v: 1 if str(v).strip().lower() in {"true", "1", "yes"} else 0)
            )

    # --- Write to SQLite using pandas (append mode) --------------------------
    fact_df.to_sql(
        name="fact_listings",
        con=conn,
        if_exists="append",   # schema already created — just append rows
        index=False,
    )
    conn.commit()

    row_count = conn.execute("SELECT COUNT(*) FROM fact_listings").fetchone()[0]
    log.info("fact_listings      → %d rows inserted.", row_count)


# =============================================================================
# Step 5 — Verify
# =============================================================================

def verify_load(df_source: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """
    Checks that the row count in fact_listings matches the source DataFrame.
    Raises a ValueError (halting execution) if there is a mismatch — per the
    mistake-free protocol, you must NOT continue to SQL queries if data is lost.
    """
    source_count = len(df_source)
    db_count     = conn.execute("SELECT COUNT(*) FROM fact_listings").fetchone()[0]

    log.info("─" * 60)
    log.info("Verification:")
    log.info("  Source CSV row count : %d", source_count)
    log.info("  DB fact_listings rows: %d", db_count)

    if source_count == db_count:
        log.info("  ✓ Row counts match — load is clean.")
    else:
        log.error("  ✗ ROW COUNT MISMATCH: %d in CSV vs %d in DB", source_count, db_count)
        raise ValueError(
            f"Row count mismatch ({source_count} vs {db_count}). "
            "Do not proceed to SQL queries. Paste this error to Claude."
        )

    # Quick spot-check: show district distribution
    log.info("─" * 60)
    log.info("District distribution (top 5 by listing count):")
    rows = conn.execute("""
        SELECT d.bezirk, COUNT(*) AS n
        FROM fact_listings f
        JOIN dim_districts d ON f.district_id = d.district_id
        GROUP BY d.bezirk
        ORDER BY n DESC
        LIMIT 5
    """).fetchall()
    for bezirk, n in rows:
        log.info("  %-35s %d", bezirk, n)


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    log.info("=" * 60)
    log.info("Phase 3 — SQLite data loader")
    log.info("=" * 60)

    # Guard: schema SQL must exist
    if not SCHEMA_SQL.exists():
        log.error("Schema file not found: %s", SCHEMA_SQL)
        log.error("Make sure sql/schema.sql exists in your project.")
        sys.exit(1)

    # Remove any existing database to start fresh every run
    if DB_PATH.exists():
        DB_PATH.unlink()
        log.info("Removed existing database to recreate from scratch.")

    # Ensure the output directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Step 1 — Load CSV
    df = load_clean_csv(CLEAN_CSV)

    # Step 2 — Create SQLite connection and run schema
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    schema_sql = SCHEMA_SQL.read_text(encoding="utf-8")
    conn.executescript(schema_sql)

    # Re-enable after executescript (executescript commits implicitly)
    conn.execute("PRAGMA foreign_keys = ON")
    log.info("Schema created: %s", SCHEMA_SQL.name)

    # Steps 3 & 4 — Populate dimensions
    district_map      = build_dim_districts(df, conn)
    property_type_map = build_dim_property_types(df, conn)

    # Step 5 — Populate fact table
    build_fact_listings(df, conn, district_map, property_type_map)

    # Step 6 — Verify
    verify_load(df, conn)

    conn.close()
    log.info("─" * 60)
    log.info("Database saved: %s", DB_PATH)
    log.info("Next step: run src/run_all_queries.py")


if __name__ == "__main__":
    main()

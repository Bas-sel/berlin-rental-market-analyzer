# Data Dictionary — Apartment Rental Offers in Germany

**Source:** ImmobilienScout24 (Germany's largest real estate platform)  
**Collected by:** corrieaar on Kaggle  
**Kaggle URL:** https://www.kaggle.com/datasets/corrieaar/apartment-rental-offers-in-germany  
**Scrape dates:** Sep18, May19, Oct19, Feb20 (four snapshots)  
**Coverage:** Germany-wide — 268,850 rows × 49 columns — filtered to Berlin in Phase 2  
**Berlin rows:** 10,406 (3.9% of full dataset)  
**License:** CC BY-NC-SA 4.0 (non-commercial use)  

---

## Column Reference

Columns are grouped by analytical importance.

### GROUP A — Core columns (zero nulls, used in every analysis)

| Column | dtype | Description | Notes |
|--------|-------|-------------|-------|
| `regio1` | object | German state (Bundesland) | `'Berlin'` for all Berlin listings — **primary filter column** |
| `regio2` | object | City / district | `'Berlin'` for all Berlin listings |
| `regio3` | object | Sub-district / neighbourhood (Kiez) | Key spatial field — maps to Bezirk in Phase 2 |
| `baseRent` | float64 | Cold rent in EUR (Kaltmiete) | **Primary target variable**. Contains placeholder values (0, 9,999,999) — filter in Phase 2 |
| `livingSpace` | float64 | Floor area in square metres | Contains placeholders (0, 111,111) — filter in Phase 2 |
| `noRooms` | float64 | Number of rooms | Includes living room; excludes kitchen/bath. Contains placeholder 999.99 — filter in Phase 2 |
| `scoutId` | int64 | Unique listing ID from ImmobilienScout24 | Appears across multiple scrape dates — deduplicate in Phase 2 |
| `date` | object | Scrape date | Values: `Sep18`, `May19`, `Oct19`, `Feb20` |

### GROUP B — Secondary columns (partial nulls, used in targeted analysis)

| Column | dtype | Null % | Description | Notes |
|--------|-------|--------|-------------|-------|
| `totalRent` | float64 | 15.1% | Warm rent in EUR (Warmmiete = baseRent + serviceCharge) | Max = 15,751,535 — placeholder errors. Prefer recalculating from baseRent + serviceCharge |
| `serviceCharge` | float64 | 2.6% | Monthly operating costs in EUR (Nebenkosten) | Max = 146,118 — placeholder. Filter > 2,000 in Phase 2 |
| `typeOfFlat` | object | 13.6% | Apartment type | Values: apartment, roof_storey, ground_floor, maisonette, penthouse, raised_ground_floor, terraced_flat, half_basement, other |
| `floor` | float64 | 19.1% | Floor number of the unit | Max = 999 — placeholder. Filter > 50 in Phase 2. -1 = basement |
| `numberOfFloors` | float64 | 36.4% | Total floors in building | Max = 999 — placeholder. Filter > 50 in Phase 2 |
| `yearConstructed` | float64 | 21.2% | Construction year | Min = 1000, Max = 2090 — errors. Filter: 1850–2024 in Phase 2 |
| `condition` | object | 25.5% | Property condition | Values: well_kept, refurbished, fully_renovated, first_time_use, mint_condition, modernized, first_time_use_after_refurbishment, need_of_renovation, negotiable |
| `interiorQual` | object | 41.9% | Interior quality rating | Values: simple, normal, sophisticated, luxury |
| `heatingType` | object | 16.7% | Heating system type | Values: central_heating, district_heating, gas_heating, self_contained_central_heating, floor_heating, oil_heating, heat_pump, combined_heat_and_power_plant, night_storage_heater, electric_heating, stove_heating, wooden_pellets, solar_heating |
| `firingTypes` | object | 21.2% | Energy source(s) for heating | **132 unique values** — stores comma-separated multi-values (e.g. `"gas,district_heating"`). Extract primary type in Phase 2 |
| `petsAllowed` | object | 42.6% | Pets permitted | Values: yes, no, negotiable |
| `lastRefurbish` | float64 | 70.0% | Year of last refurbishment | Max = 2919 (typo for 2019). Filter: ≤ 2024 in Phase 2 |
| `pricetrend` | float64 | 0.7% | Platform-generated price trend score | Range: -12.33 to 14.92. Meaning: positive = rising local prices |

### GROUP C — Amenity flags (boolean, zero nulls)

| Column | dtype | Description |
|--------|-------|-------------|
| `hasKitchen` | bool | Fitted/built-in kitchen included (Einbauküche) |
| `cellar` | bool | Unit has private cellar storage |
| `balcony` | bool | Unit has balcony |
| `garden` | bool | Unit has garden access |
| `lift` | bool | Building has elevator |
| `newlyConst` | bool | Newly constructed building |

### GROUP D — Address fields

| Column | dtype | Null % | Description | Notes |
|--------|-------|--------|-------------|-------|
| `streetPlain` | object | 26.4% | Clean street name (UTF-8 decoded) | **Use this column**, not `street` |
| `street` | object | 0% | Street name with HTML entities (e.g. `Sch&uuml;ruferstra&szlig;e`) | Duplicate of `streetPlain` with encoding issues — **drop in Phase 2** |
| `houseNumber` | object | 26.4% | Street number | Low analytical value |
| `geo_plz` | int64 | 0% | Postal code (PLZ) | Useful for granular spatial joins |

### GROUP E — Redundant geography columns (drop in Phase 2)

| Column | dtype | Description | Why drop |
|--------|-------|-------------|----------|
| `geo_bln` | object | **Identical to `regio1`** — same 16 states, same row counts | Complete duplicate |
| `geo_krs` | object | **Identical to `regio2`** — same 419 cities, same row counts | Complete duplicate |
| `yearConstructedRange` | float64 | Discretised band of `yearConstructed` | Prefer raw `yearConstructed` |
| `baseRentRange` | int64 | Discretised band of `baseRent` | Prefer raw `baseRent` |
| `livingSpaceRange` | int64 | Discretised band of `livingSpace` | Prefer raw `livingSpace` |
| `noRoomsRange` | int64 | Discretised band of `noRooms` | Prefer raw `noRooms` |

### GROUP F — Low-value columns (drop in Phase 2)

| Column | dtype | Null % | Reason to drop |
|--------|-------|--------|----------------|
| `telekomHybridUploadSpeed` | float64 | 83.2% | Constant value (10.0) — zero variance, zero analytical value |
| `electricityKwhPrice` | float64 | 82.6% | Near-constant (nearly all values = 0.20) — not listing-specific |
| `electricityBasePrice` | float64 | 82.6% | Near-constant (nearly all values = 90.76) — not listing-specific |
| `energyEfficiencyClass` | object | 71.1% | 71% nulls — too sparse for analysis |
| `heatingCosts` | float64 | 68.2% | 68% nulls — too sparse |
| `noParkSpaces` | float64 | 65.4% | 65% nulls, not relevant to rental market analysis |
| `thermalChar` | float64 | 39.6% | Energy consumption kWh/m²yr — contains errors (max = 1996) |
| `telekomTvOffer` | object | 12.1% | Telekom promotional field — not rental market data |
| `telekomUploadSpeed` | float64 | 12.4% | Telekom promotional field — not rental market data |
| `picturecount` | int64 | 0% | Listing quality proxy — not rental market data |

### GROUP G — Free-text columns (informational only)

| Column | dtype | Null % | Description |
|--------|-------|--------|-------------|
| `description` | object | 7.3% | Full listing description in German — not used for quantitative analysis |
| `facilities` | object | 19.7% | Building/unit facilities in German — not used for quantitative analysis |

---

## Key Derived Columns (created in Phase 2)

| Column | Formula | Purpose |
|--------|---------|---------|
| `price_per_sqm` | `baseRent / livingSpace` | Normalised price — primary analysis metric |
| `size_category` | bins on `livingSpace`: <40, 40–65, 65–90, >90 m² | Micro / Small / Medium / Large |
| `district_tier` | grouping of `regio3` mapped to Bezirk | Premium / Mid / Affordable |
| `era` | bins on `yearConstructed`: <1918, 1918–45, 1946–90, >1990 | Construction era — relevant for Berlin |

---

## Outlier / Placeholder Value Reference

These values must be filtered out in Phase 2. They are data entry placeholders, not real listings.

| Column | Threshold | Action |
|--------|-----------|--------|
| `baseRent` | Keep 100 ≤ value ≤ 10,000 | Drop rows outside range |
| `livingSpace` | Keep 10 ≤ value ≤ 500 | Drop rows outside range |
| `noRooms` | Keep value ≤ 20 | Drop rows above |
| `yearConstructed` | Keep 1850 ≤ value ≤ 2024 | Drop rows outside range |
| `serviceCharge` | Keep value ≤ 2,000 | Drop rows above |
| `floor` | Keep value ≤ 50 | Drop rows above |
| `numberOfFloors` | Keep value ≤ 50 | Drop rows above |

---

## Deduplication Note

The dataset contains **four scrape dates** (Sep18, May19, Oct19, Feb20). The same listing (`scoutId`) can appear in multiple snapshots with 0 exact duplicates because the `date` column differs. In Phase 2, deduplicate by keeping the most recent entry per `scoutId` (`date == 'Feb20'` takes priority, then Oct19, then May19, then Sep18).

---

## Berlin Bezirke Reference

The `regio3` column contains Kiez-level names. Berlin's 12 official Bezirke are:

| Bezirk | General Character |
|--------|-------------------|
| Mitte | Central, highest prices |
| Friedrichshain-Kreuzberg | Trendy, young, mixed |
| Pankow | Family-friendly, north |
| Charlottenburg-Wilmersdorf | Upscale, west |
| Spandau | Affordable, outer west |
| Steglitz-Zehlendorf | Suburban, south-west |
| Tempelhof-Schöneberg | Mixed, central-south |
| Neukölln | Up-and-coming, south |
| Treptow-Köpenick | Suburban, south-east |
| Marzahn-Hellersdorf | Affordable, east |
| Lichtenberg | Mixed, east |
| Reinickendorf | Suburban, north |

---

## Important Rules

- **Do not modify the raw CSV.** All filtering and cleaning happens in `src/cleaning_pipeline.py` (Phase 2).
- **Filter to Berlin first** in Phase 2: `df[df['regio1'] == 'Berlin']` before any analysis.
- **Deduplicate on `scoutId`** keeping the Feb20 record as described above.

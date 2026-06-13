"""
visualizations.py
=================
Phase 4 — Python Visualisations
Berlin Rental Market Analyzer

Produces 10 publication-quality charts from the cleaned Berlin rental dataset
and saves each one as a 300-dpi PNG to reports/figures/.

Charts produced
---------------
  01  01_avg_rent_by_bezirk.png              Avg monthly base rent per district (horizontal bar)
  02  02_rent_distribution.png               Distribution of base rents (histogram + KDE)
  03  03_price_per_sqm_by_bezirk.png         Avg price per m² per district (horizontal bar)
  04  04_rent_by_property_type.png           Rent spread by flat type (horizontal box plot)
  05  05_area_vs_rent_scatter.png            Floor area vs. rent by district tier (scatter)
  06  06_correlation_heatmap.png             Correlation matrix of numeric features
  07  07_rent_by_size_category.png           Rent distribution by apartment size (violin)
  08  08_rent_by_era.png                     Rent & price/m² by construction era (grouped bar)
  09  09_amenity_impact.png                  Amenity impact on average rent (grouped bar)
  10  10_price_per_sqm_dist_by_bezirk.png    Price/m² distribution per district (box plot)

How to run
----------
  Activate the conda environment and run from the PROJECT ROOT directory:

    conda activate berlin_rental
    python src/visualizations.py

  All output PNGs will appear in reports/figures/.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import sys

# ── Third-party ───────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable


# =============================================================================
# PATHS
# =============================================================================
# All paths are relative to the project root directory.
# Run this script with:  python src/visualizations.py
# NOT with:              python visualizations.py   (from inside src/)

CLEAN_CSV   = os.path.join("data", "clean", "berlin_listings_clean.csv")
FIGURES_DIR = os.path.join("reports", "figures")


# =============================================================================
# VISUAL STYLE
# =============================================================================
# Every styling decision lives here.  Changing a value in this section
# propagates automatically to all 10 charts, keeping the suite consistent.

# ── Matplotlib base style ─────────────────────────────────────────────────────
# "seaborn-v0_8-whitegrid" is the correct name in seaborn >= 0.12.
# The try/except falls back to the older name for environments with
# seaborn < 0.12 installed.
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("seaborn-whitegrid")

plt.rcParams.update({
    # Font — Arial is the cleanest option on Windows; DejaVu Sans is the fallback
    "font.family":       "sans-serif",
    "font.sans-serif":   ["Arial", "DejaVu Sans", "Helvetica", "sans-serif"],
    "font.size":         11,

    # Axes text sizes
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "axes.titlepad":     12,
    "axes.labelsize":    11,
    "axes.labelpad":     6,

    # Remove the top and right borders from every chart automatically
    "axes.spines.top":   False,
    "axes.spines.right": False,

    # Tick label sizes
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,

    # Legend
    "legend.fontsize":   10,
    "legend.framealpha": 0.9,

    # DPI settings
    # figure.dpi controls the on-screen preview in PyCharm
    # savefig.dpi controls the exported PNG — always 300 for portfolio quality
    "figure.dpi":        120,
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
})

# ── Colour palette ────────────────────────────────────────────────────────────
PRIMARY_BLUE  = "#2D6A9F"   # main colour for single-series charts
HIGHLIGHT_RED = "#C0392B"   # accent (city-average lines, premium annotations)
NEUTRAL_GREY  = "#AAAAAA"   # non-highlighted elements, footnote text

# District tier: green = affordable, blue = mid, red = premium
# Ordered from cheapest to most expensive to match how the analysis reads.
TIER_ORDER = ["Affordable", "Mid", "Premium"]
TIER_PALETTE = {
    "Affordable": "#55A868",
    "Mid":        "#4C72B0",
    "Premium":    "#C44E52",
}

# Size category: light blue (small) → dark blue (large)
SIZE_ORDER = ["Micro", "Small", "Medium", "Large"]
SIZE_PALETTE = {
    "Micro":  "#A8D0E8",
    "Small":  "#5DA0C8",
    "Medium": "#2D78A8",
    "Large":  "#1A4A6E",
}

# Construction era: earthy tones for historic, cooler tones for modern
ERA_ORDER = ["Pre-1918", "1918–1945", "1946–1990", "Post-1990"]
ERA_PALETTE = {
    "Pre-1918":  "#7B5C1C",
    "1918–1945": "#C9943A",
    "1946–1990": "#7EA6C4",
    "Post-1990": "#2D6A9F",
}

# Sequential colourmap for ranking charts (low value = light, high = dark)
SEQ_CMAP = "YlOrRd"

# Diverging colourmap for the correlation heatmap (negative = blue, positive = red)
DIV_CMAP = "RdBu_r"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def save_figure(fig: plt.Figure, filename: str) -> None:
    """
    Save a finished figure as a 300-dpi PNG to reports/figures/.

    Parameters
    ----------
    fig      : the matplotlib Figure to save
    filename : file name only, e.g. "01_avg_rent_by_bezirk.png"
               The directory prefix is added automatically.
    """
    os.makedirs(FIGURES_DIR, exist_ok=True)
    output_path = os.path.join(FIGURES_DIR, filename)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  ✓  Saved → {output_path}")
    plt.close(fig)


def eur_formatter(x: float, pos=None) -> str:
    """
    Matplotlib axis formatter that renders numeric values as Euro amounts.

    Examples
    --------
    1200   → "€1,200"
    850.5  → "€851"
    """
    return f"€{x:,.0f}"


def footnote(ax: plt.Axes, text: str) -> None:
    """
    Add a small grey data-source note below an axes.

    Placed in axes-fraction coordinates so it never overlaps chart content,
    and is always captured by bbox_inches='tight' when saving.

    Parameters
    ----------
    ax   : the axes to annotate
    text : the footnote string (typically data source + sample size)
    """
    ax.text(
        0.0, -0.10,
        text,
        transform=ax.transAxes,
        fontsize=8,
        color=NEUTRAL_GREY,
        va="top",
    )


def to_bool_series(series: pd.Series) -> pd.Series:
    """
    Safely convert a column to a proper boolean Series.

    When bool columns (hasKitchen, balcony, etc.) are written to CSV
    and read back with pd.read_csv, pandas stores them as the strings
    "True" and "False" (object dtype) rather than as Python booleans.
    This helper handles both forms reliably.

    Parameters
    ----------
    series : a pandas Series that may be dtype bool or dtype object

    Returns
    -------
    pd.Series of dtype bool
    """
    if series.dtype in (bool, np.bool_):
        return series.astype(bool)
    # String round-trip from CSV: "True" / "False"
    return series.astype(str).str.strip().str.lower().map({"true": True, "false": False})


def load_data() -> pd.DataFrame:
    """
    Load the cleaned Berlin listings CSV and prepare it for visualisation.

    Actions taken
    -------------
    - Verifies the file exists (exits with a helpful message if not)
    - Checks the expected row count of 10,369
    - Casts size_category, era, and district_tier to ordered Categoricals
      with the confirmed sort orders so that groupby and plot ordering
      work correctly throughout

    Returns
    -------
    pd.DataFrame  10,369 rows × 35 columns
    """
    print("Loading cleaned dataset …")

    if not os.path.exists(CLEAN_CSV):
        sys.exit(
            f"\n  ✗  File not found: {CLEAN_CSV}\n"
            f"     Make sure you are running this script from the project root,\n"
            f"     not from inside src/.  Expected command:\n"
            f"       python src/visualizations.py\n"
        )

    df = pd.read_csv(CLEAN_CSV)

    expected_rows = 10_369
    actual_rows   = len(df)

    if actual_rows != expected_rows:
        print(
            f"  ⚠  WARNING — expected {expected_rows:,} rows but found {actual_rows:,}. "
            f"Proceeding anyway."
        )
    else:
        print(f"  ✓  {actual_rows:,} rows loaded.")

    # Apply ordered Categorical dtypes so that sort operations on these columns
    # always respect the logical sequence (e.g., Micro before Small, not alphabetical).
    df["size_category"] = pd.Categorical(
        df["size_category"], categories=SIZE_ORDER, ordered=True
    )
    df["era"] = pd.Categorical(
        df["era"], categories=ERA_ORDER, ordered=True
    )
    df["district_tier"] = pd.Categorical(
        df["district_tier"], categories=TIER_ORDER, ordered=True
    )

    return df


# =============================================================================
# CHART FUNCTIONS
# =============================================================================

def chart_01_avg_rent_by_bezirk(df: pd.DataFrame) -> None:
    """
    Chart 01 — Average Monthly Base Rent by Berlin District

    A horizontal bar chart that ranks all 12 Bezirke by their mean base rent.
    Bars are coloured with a sequential warm palette (yellow → red) so the
    price gradient is immediately visible.  A dashed vertical line marks
    the city-wide average for quick reference.

    Why this chart:
        The Bezirk comparison is the most natural question any Berlin renter
        asks.  It anchors all subsequent analysis by establishing which
        districts are expensive and which are affordable.
    """
    print("\nChart 01 — Avg Rent by Bezirk …")

    # Compute mean base rent per district.
    # Sorted ascending so the most expensive district ends up at the TOP
    # of the horizontal chart (the bar chart reads top-to-bottom naturally).
    grouped = (
        df.groupby("bezirk")["baseRent"]
        .mean()
        .sort_values(ascending=True)
        .reset_index()
    )
    grouped.columns = ["bezirk", "avg_rent"]

    # Colour each bar on a sequential scale from the minimum to maximum value
    norm   = Normalize(vmin=grouped["avg_rent"].min(), vmax=grouped["avg_rent"].max())
    cmap   = plt.get_cmap(SEQ_CMAP)
    colors = [cmap(norm(v)) for v in grouped["avg_rent"]]

    fig, ax = plt.subplots(figsize=(10, 7))

    bars = ax.barh(
        grouped["bezirk"],
        grouped["avg_rent"],
        color=colors,
        height=0.68,
    )

    # Value label to the right of each bar
    for bar, val in zip(bars, grouped["avg_rent"]):
        ax.text(
            bar.get_width() + 20,
            bar.get_y() + bar.get_height() / 2,
            f"€{val:,.0f}",
            va="center",
            ha="left",
            fontsize=9,
            color="#333333",
        )

    # Colour bar as a visual legend
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.5, pad=0.02)
    cbar.set_label("Avg Monthly Rent (€)", fontsize=9)
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))
    cbar.ax.tick_params(labelsize=8)

    # City-average reference line
    # get_xaxis_transform() lets us specify x in data coords but y as an
    # axes fraction (0 = bottom, 1 = top), which keeps the label visible
    # regardless of how many Bezirke are plotted.
    city_avg = df["baseRent"].mean()
    ax.axvline(
        city_avg,
        color=HIGHLIGHT_RED,
        linestyle="--",
        linewidth=1.5,
        alpha=0.85,
    )
    ax.text(
        city_avg + 10,
        0.52,
        f"City avg\n€{city_avg:,.0f}",
        color=HIGHLIGHT_RED,
        fontsize=8.5,
        va="bottom",
        transform=ax.get_xaxis_transform(),
    )

    ax.set_xlabel("Average Monthly Base Rent (€)")
    ax.set_title("Average Monthly Base Rent by Berlin District")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))
    ax.set_xlim(left=0, right=grouped["avg_rent"].max() * 1.20)

    footnote(ax, "Data: ImmobilienScout24 via Kaggle (corrieaar) — n = 10,369 Berlin listings")

    plt.tight_layout()
    save_figure(fig, "01_avg_rent_by_bezirk.png")


def chart_02_rent_distribution(df: pd.DataFrame) -> None:
    """
    Chart 02 — Distribution of Monthly Base Rent

    A histogram with a KDE (kernel density estimate) overlay showing the
    full shape of the rent distribution across all 10,369 listings.
    Vertical dashed lines mark the mean and median.

    The gap between mean and median quantifies the right skew: a small
    number of high-priced luxury listings pull the mean above the median.

    Why this chart:
        Before segmenting by any dimension, a recruiter reviewing the
        portfolio needs to understand the overall rent landscape.
        This chart also provides the key summary statistics in a
        self-contained annotation box so the chart works standalone.
    """
    print("Chart 02 — Rent Distribution …")

    fig, ax = plt.subplots(figsize=(10, 6))

    # histplot with kde=True draws both histogram bars and the KDE curve
    # in a single Seaborn call, matching the colour automatically.
    sns.histplot(
        df["baseRent"],
        bins=50,
        kde=True,
        color=PRIMARY_BLUE,
        alpha=0.60,
        ax=ax,
        line_kws={"linewidth": 2.0},
    )

    mean_rent   = df["baseRent"].mean()
    median_rent = df["baseRent"].median()

    ax.axvline(
        mean_rent,
        color="#C0392B",
        linestyle="--",
        linewidth=1.8,
        label=f"Mean   €{mean_rent:,.0f}",
    )
    ax.axvline(
        median_rent,
        color="#27AE60",
        linestyle="--",
        linewidth=1.8,
        label=f"Median €{median_rent:,.0f}",
    )

    # Summary stats annotation box — monospaced font so numbers align cleanly
    stats_text = (
        f"n = {len(df):,}\n"
        f"Mean   = €{mean_rent:,.0f}\n"
        f"Median = €{median_rent:,.0f}\n"
        f"Std    = €{df['baseRent'].std():,.0f}\n"
        f"Q1     = €{df['baseRent'].quantile(0.25):,.0f}\n"
        f"Q3     = €{df['baseRent'].quantile(0.75):,.0f}"
    )
    ax.text(
        0.98, 0.95,
        stats_text,
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
        ha="right",
        family="monospace",
        bbox=dict(
            boxstyle="round,pad=0.5",
            facecolor="white",
            alpha=0.85,
            edgecolor="#CCCCCC",
        ),
    )

    ax.set_xlabel("Monthly Base Rent (€)")
    ax.set_ylabel("Number of Listings")
    ax.set_title("Distribution of Monthly Base Rent — Berlin Rental Market")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))
    ax.legend(frameon=True)

    footnote(ax, "Data: ImmobilienScout24 via Kaggle (corrieaar) — n = 10,369 Berlin listings")

    plt.tight_layout()
    save_figure(fig, "02_rent_distribution.png")


def chart_03_price_per_sqm_by_bezirk(df: pd.DataFrame) -> None:
    """
    Chart 03 — Average Rent Price per m² by Berlin District

    Same horizontal bar structure as Chart 01 but using price_per_sqm
    instead of raw baseRent.

    Dividing by floor area removes the size-confounding effect: a district
    where listings happen to be large will show a higher average rent but
    not necessarily a higher price per m².  This chart gives the
    like-for-like comparison.

    Why this chart:
        Comparing raw rent across districts without normalising for size
        is misleading.  Presenting both Chart 01 and Chart 03 together
        shows analytical rigour — you know the difference matters.
    """
    print("Chart 03 — Price per m² by Bezirk …")

    grouped = (
        df.groupby("bezirk")["price_per_sqm"]
        .mean()
        .sort_values(ascending=True)
        .reset_index()
    )
    grouped.columns = ["bezirk", "avg_ppsqm"]

    norm   = Normalize(vmin=grouped["avg_ppsqm"].min(), vmax=grouped["avg_ppsqm"].max())
    cmap   = plt.get_cmap(SEQ_CMAP)
    colors = [cmap(norm(v)) for v in grouped["avg_ppsqm"]]

    fig, ax = plt.subplots(figsize=(10, 7))

    bars = ax.barh(
        grouped["bezirk"],
        grouped["avg_ppsqm"],
        color=colors,
        height=0.68,
    )

    for bar, val in zip(bars, grouped["avg_ppsqm"]):
        ax.text(
            bar.get_width() + 0.06,
            bar.get_y() + bar.get_height() / 2,
            f"€{val:.2f}/m²",
            va="center",
            ha="left",
            fontsize=9,
            color="#333333",
        )

    # Colour bar legend
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.5, pad=0.02)
    cbar.set_label("Avg Price per m² (€)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    # City average line
    city_avg_ppsqm = df["price_per_sqm"].mean()
    ax.axvline(
        city_avg_ppsqm,
        color=HIGHLIGHT_RED,
        linestyle="--",
        linewidth=1.5,
        alpha=0.85,
    )
    ax.text(
        city_avg_ppsqm + 0.04,
        0.52,
        f"City avg\n€{city_avg_ppsqm:.2f}/m²",
        color=HIGHLIGHT_RED,
        fontsize=8.5,
        va="bottom",
        transform=ax.get_xaxis_transform(),
    )

    ax.set_xlabel("Average Price per m² (€)")
    ax.set_title("Average Rent Price per m² by Berlin District")
    ax.set_xlim(left=0, right=grouped["avg_ppsqm"].max() * 1.20)

    footnote(ax, "Data: ImmobilienScout24 via Kaggle (corrieaar) — n = 10,369 Berlin listings")

    plt.tight_layout()
    save_figure(fig, "03_price_per_sqm_by_bezirk.png")


def chart_04_rent_by_property_type(df: pd.DataFrame) -> None:
    """
    Chart 04 — Base Rent Distribution by Property Type

    Horizontal box plots — one per flat type — sorted by median rent
    so the most expensive type sits at the top.

    Choosing a box plot over a bar of means is a deliberate analytical
    decision: it shows the full distribution (Q1, median, Q3, and
    outlier points) rather than a single summary statistic.  Wide boxes
    signal heterogeneous listings within that type; narrow boxes suggest
    consistent pricing.

    Why this chart:
        A portfolio project that only shows means looks superficial.
        This chart demonstrates that you understand the difference between
        central tendency and distribution.
    """
    print("Chart 04 — Rent by Property Type (box plot) …")

    # typeOfFlat has ~13.6% nulls — drop them for this chart
    # and record how many rows remain for the footnote
    df_flat = df.dropna(subset=["typeOfFlat"]).copy()
    n_used  = len(df_flat)

    # Sort flat types by their median base rent (ascending = highest at top of chart)
    type_order = (
        df_flat.groupby("typeOfFlat")["baseRent"]
        .median()
        .sort_values(ascending=True)
        .index.tolist()
    )
    median_vals = df_flat.groupby("typeOfFlat")["baseRent"].median()

    fig, ax = plt.subplots(figsize=(11, 7))

    sns.boxplot(
        data=df_flat,
        x="baseRent",
        y="typeOfFlat",
        order=type_order,
        color=PRIMARY_BLUE,
        flierprops=dict(
            marker="o",
            markerfacecolor=NEUTRAL_GREY,
            markersize=2.5,
            alpha=0.40,
            linestyle="none",
        ),
        linewidth=0.9,
        ax=ax,
    )

    # Annotate each row with its median value.
    # The offset is 2% of the Q3 value so it scales with the data range.
    x_offset = df_flat["baseRent"].quantile(0.75) * 0.02
    for i, ftype in enumerate(type_order):
        med = median_vals[ftype]
        ax.text(
            med + x_offset,
            i,
            f"€{med:,.0f}",
            va="center",
            ha="left",
            fontsize=8.5,
            color="#333333",
        )

    ax.set_xlabel("Monthly Base Rent (€)")
    ax.set_ylabel("")   # flat type names are self-explanatory on the y-axis
    ax.set_title("Base Rent Distribution by Property Type")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))

    # Cap x-axis at 98th percentile so a few extreme outliers don't compress
    # the main chart area where most listings live
    ax.set_xlim(left=0, right=df_flat["baseRent"].quantile(0.98) * 1.15)

    ax.text(
        0.98, 0.02,
        f"n = {n_used:,}  (rows with missing typeOfFlat excluded)",
        transform=ax.transAxes,
        fontsize=8,
        ha="right",
        color=NEUTRAL_GREY,
    )
    footnote(ax, "Data: ImmobilienScout24 via Kaggle (corrieaar)")

    plt.tight_layout()
    save_figure(fig, "04_rent_by_property_type.png")


def chart_05_area_vs_rent_scatter(df: pd.DataFrame) -> None:
    """
    Chart 05 — Floor Area vs Monthly Rent by District Tier

    A scatter plot with livingSpace on the x-axis and baseRent on the
    y-axis.  Each point is coloured by its district_tier category.

    Low alpha (0.18) manages the overplotting that comes with ~10,000 points.
    A linear regression line is drawn for each tier separately to show
    whether the area-to-rent slope differs by market segment.

    Both axes are capped at the 99th percentile: a handful of luxury
    outliers would otherwise compress the 95% of listings that matter most.

    Why this chart:
        Three variables in one view — area, rent, and district tier —
        with a regression overlay to quantify the relationship.
        This demonstrates multivariate thinking clearly.
    """
    print("Chart 05 — Scatter: Floor Area vs Rent …")

    # Exclude the extreme tail on both axes
    area_cap = df["livingSpace"].quantile(0.99)
    rent_cap = df["baseRent"].quantile(0.99)
    df_plot  = df[
        (df["livingSpace"] <= area_cap) &
        (df["baseRent"]    <= rent_cap)
    ].copy()

    fig, ax = plt.subplots(figsize=(11, 7))

    for tier in TIER_ORDER:
        subset = df_plot[df_plot["district_tier"] == tier]

        ax.scatter(
            subset["livingSpace"],
            subset["baseRent"],
            color=TIER_PALETTE[tier],
            alpha=0.18,
            s=12,
            label=f"{tier}  (n={len(subset):,})",
        )

        # Draw a regression line only when there are enough points to be meaningful
        if len(subset) >= 20:
            slope, intercept = np.polyfit(
                subset["livingSpace"],
                subset["baseRent"],
                deg=1,
            )
            x_line = np.linspace(
                subset["livingSpace"].min(),
                subset["livingSpace"].max(),
                200,
            )
            ax.plot(
                x_line,
                slope * x_line + intercept,
                color=TIER_PALETTE[tier],
                linewidth=2.0,
                alpha=0.90,
            )

    ax.set_xlabel("Floor Area (m²)")
    ax.set_ylabel("Monthly Base Rent (€)")
    ax.set_title("Floor Area vs Monthly Rent by District Tier")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))

    # Larger marker scale in the legend so the colours are clearly distinguishable
    ax.legend(
        frameon=True,
        title="District Tier",
        markerscale=3,
        title_fontsize=10,
    )

    footnote(
        ax,
        "Data: ImmobilienScout24 via Kaggle (corrieaar)  —  "
        "axes capped at 99th percentile  |  lines show OLS regression per tier",
    )

    plt.tight_layout()
    save_figure(fig, "05_area_vs_rent_scatter.png")


def chart_06_correlation_heatmap(df: pd.DataFrame) -> None:
    """
    Chart 06 — Correlation Matrix of Key Numeric Features

    A lower-triangle Pearson correlation heatmap covering the main
    numeric columns.  The upper triangle is masked to avoid redundancy
    (the matrix is symmetric, so showing both halves adds no information).

    Columns included:
        baseRent, livingSpace, noRooms, price_per_sqm,
        floor, serviceCharge, yearConstructed, pricetrend

    NaN values in any column are handled pairwise by pandas .corr(),
    so rows with nulls in one column still contribute to correlations
    between the other columns.

    Why this chart:
        A standard EDA deliverable.  It shows at a glance which features
        are correlated with rent (useful feature selection signal) and
        where multicollinearity exists (e.g., livingSpace ↔ noRooms).
    """
    print("Chart 06 — Correlation Heatmap …")

    wanted_cols = [
        "baseRent",
        "livingSpace",
        "noRooms",
        "price_per_sqm",
        "floor",
        "serviceCharge",
        "yearConstructed",
        "pricetrend",
    ]

    # Only include columns that actually exist — defensive against column name changes
    available = [c for c in wanted_cols if c in df.columns]
    corr      = df[available].corr()

    # Mask the upper triangle (True = hidden) so only the lower half renders
    mask = np.triu(np.ones_like(corr, dtype=bool))

    fig, ax = plt.subplots(figsize=(9, 7))

    sns.heatmap(
        corr,
        mask=mask,
        cmap=DIV_CMAP,
        vmin=-1,
        vmax=1,
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        linecolor="#DDDDDD",
        square=True,
        ax=ax,
        cbar_kws={"shrink": 0.75, "label": "Pearson r"},
        annot_kws={"size": 9},
    )

    ax.set_title("Correlation Matrix of Key Numeric Features")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0,  fontsize=9)

    footnote(ax, "Data: ImmobilienScout24 via Kaggle (corrieaar) — n = 10,369 Berlin listings")

    plt.tight_layout()
    save_figure(fig, "06_correlation_heatmap.png")


def chart_07_rent_by_size_category(df: pd.DataFrame) -> None:
    """
    Chart 07 — Base Rent Distribution by Apartment Size Category

    Violin plots across the four ordered size categories
    (Micro → Small → Medium → Large).  The inner quartile lines show
    Q1, median, and Q3 inside each violin shape.  A white dot marks
    the mean of each group.

    The violin shape reveals whether rent spreads symmetrically within
    each size band or has a long upper tail (i.e., luxury listings
    skewing the distribution upward for larger flats).

    Sample sizes are embedded in the x-axis tick labels so the chart
    is self-contained.

    Why this chart:
        A violin plot is a step up from a bar of means.  Choosing it
        over a simple bar chart signals that you understand distributions,
        not just averages.
    """
    print("Chart 07 — Rent by Size Category (violin) …")

    # Count per category for the x-axis tick labels
    counts = (
        df.groupby("size_category", observed=True)
        .size()
        .reindex(SIZE_ORDER)
    )

    # Mean per category for the overlay dot
    means = (
        df.groupby("size_category", observed=True)["baseRent"]
        .mean()
        .reindex(SIZE_ORDER)
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    # FIX: seaborn >= 0.13 requires the grouping column to be assigned to
    # 'hue' explicitly.  Pass the palette as a dict (category → colour)
    # and suppress the redundant legend with legend=False.
    sns.violinplot(
        data=df,
        x="size_category",
        y="baseRent",
        order=SIZE_ORDER,
        hue="size_category",
        palette={cat: SIZE_PALETTE[cat] for cat in SIZE_ORDER},
        legend=False,
        inner="quartile",   # draws Q1, median, Q3 as lines inside each violin
        linewidth=0.8,
        ax=ax,
    )

    # White dot = mean, drawn on top of each violin
    for i, cat in enumerate(SIZE_ORDER):
        mean_val = means[cat]
        if pd.notna(mean_val):
            ax.scatter(i, mean_val, color="white", s=40, zorder=5, linewidths=0)

    # FIX: call set_xticks() first to lock the tick positions, then
    # set_xticklabels() to overwrite them.  Without set_xticks() first,
    # matplotlib raises a UserWarning about an unfixed tick locator.
    tick_labels = [
        f"{cat}\n(n={int(counts[cat]):,})" if pd.notna(counts[cat]) else cat
        for cat in SIZE_ORDER
    ]
    ax.set_xticks(range(len(SIZE_ORDER)))
    ax.set_xticklabels(tick_labels, fontsize=9)

    ax.set_xlabel("")   # tick labels carry the category name already
    ax.set_ylabel("Monthly Base Rent (€)")
    ax.set_title("Base Rent Distribution by Apartment Size Category")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))

    footnote(ax, "Data: ImmobilienScout24 via Kaggle (corrieaar) — n = 10,369 Berlin listings")

    plt.tight_layout()
    save_figure(fig, "07_rent_by_size_category.png")

def chart_08_rent_by_era(df: pd.DataFrame) -> None:
    """
    Chart 08 — Average Rent and Price per m² by Construction Era

    A grouped bar chart with two bars per era:
      • solid bar   — average monthly base rent (left y-axis, €)
      • hatched bar — average price per m²      (right y-axis, €/m²)

    Using dual y-axes is a deliberate choice here: the two metrics are on
    different scales and both belong on the same chart because they tell
    complementary stories about each time period.

    The four Berlin construction eras are historically meaningful:
      Pre-1918   — Altbau (high ceilings, ornate facades, sought-after)
      1918–1945  — Weimar Republic and early modernist construction
      1946–1990  — Divided city (East: Plattenbau / West: postwar social housing)
      Post-1990  — Reunification era and contemporary new-builds

    Why this chart:
        Connecting urban history to current market prices is exactly the
        kind of Berlin-specific insight that makes a portfolio project
        stand out to a German recruiter.
    """
    print("Chart 08 — Rent by Construction Era (grouped bar) …")

    # Drop rows where era is null (listings with missing or out-of-range yearConstructed)
    df_era = df.dropna(subset=["era"]).copy()

    era_stats = (
        df_era
        .groupby("era", observed=True)
        .agg(
            avg_rent  = ("baseRent",      "mean"),
            avg_ppsqm = ("price_per_sqm", "mean"),
            count     = ("baseRent",      "count"),
        )
        .reindex(ERA_ORDER)   # enforce the chronological order we defined
        .reset_index()
    )

    x          = np.arange(len(ERA_ORDER))
    width      = 0.36
    era_colors = [ERA_PALETTE[e] for e in ERA_ORDER]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()   # second y-axis that shares the same x-axis

    # Left axis: solid bars = avg monthly rent
    bars1 = ax1.bar(
        x - width / 2,
        era_stats["avg_rent"],
        width,
        color=era_colors,
        alpha=0.90,
    )

    # Right axis: hatched bars = avg price per m²
    bars2 = ax2.bar(
        x + width / 2,
        era_stats["avg_ppsqm"],
        width,
        color=era_colors,
        alpha=0.50,
        hatch="///",
    )

    # FIX: guard every bar annotation with np.isfinite().
    # If a bar has a NaN height (e.g., an era with no matching rows after
    # reindex), bar.get_height() returns NaN, and matplotlib would then
    # try to draw text at y=NaN, producing "posx and posy should be
    # finite values" once per bar.  The guard skips those cases cleanly.
    for bar in bars1:
        height = bar.get_height()
        if not np.isfinite(height):
            continue
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height + 8,
            f"€{height:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
        )

    for bar in bars2:
        height = bar.get_height()
        if not np.isfinite(height):
            continue
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.08,
            f"€{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
        )

    # Embed sample counts in the x-axis tick labels
    tick_labels = []
    for i, era in enumerate(ERA_ORDER):
        count_val = era_stats.loc[i, "count"]
        if pd.notna(count_val):
            tick_labels.append(f"{era}\n(n={int(count_val):,})")
        else:
            tick_labels.append(era)

    ax1.set_xticks(x)
    ax1.set_xticklabels(tick_labels, fontsize=9)

    ax1.set_ylabel("Average Monthly Base Rent (€)", labelpad=8)
    ax2.set_ylabel("Average Price per m² (€/m²)",  labelpad=8)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))
    ax1.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)
    ax2.spines["top"].set_visible(False)

    ax1.set_title("Average Rent and Price per m² by Construction Era")

    # Manual legend: one patch per bar style
    patch_solid   = mpatches.Patch(
        color="#7B5C1C", alpha=0.90,
        label="Avg Monthly Rent (solid bar)",
    )
    patch_hatched = mpatches.Patch(
        color="#7B5C1C", alpha=0.50, hatch="///",
        label="Avg Price per m² (hatched bar)",
    )
    ax1.legend(handles=[patch_solid, patch_hatched], loc="upper left", frameon=True, fontsize=9)

    footnote(
        ax1,
        "Data: ImmobilienScout24 via Kaggle (corrieaar)  —  "
        "listings without a valid yearConstructed are excluded",
    )

    plt.tight_layout()
    save_figure(fig, "08_rent_by_era.png")

def chart_09_amenity_impact(df: pd.DataFrame) -> None:
    """
    Chart 09 — Impact of Key Amenities on Average Monthly Rent

    For each of the five boolean amenity columns (hasKitchen, balcony,
    cellar, garden, lift), this chart computes the average baseRent for
    listings where the amenity is present (True) versus absent (False).

    Amenities are sorted from highest to lowest premium (absolute
    difference between the two bars) so the chart reads left-to-right
    in order of economic impact.

    An annotation above each pair of bars shows the premium amount,
    coloured red for a positive premium and green for a negative one.

    Note on interpretation:
        This chart shows correlation, not causation.  Higher-end apartments
        tend to have all amenities simultaneously, so part of the measured
        premium reflects overall apartment quality rather than the
        amenity itself.

    Why this chart:
        Boolean flag columns are easy to query but their economic impact
        is rarely visualised.  Doing so shows you think beyond descriptive
        statistics into actionable insight.
    """
    print("Chart 09 — Amenity Impact …")

    amenity_cols = {
        "hasKitchen": "Fitted Kitchen",
        "balcony":    "Balcony",
        "cellar":     "Cellar",
        "garden":     "Garden",
        "lift":       "Lift / Elevator",
    }

    rows = []
    for col, label in amenity_cols.items():
        if col not in df.columns:
            print(f"  ⚠  Column '{col}' not found in DataFrame — skipping.")
            continue

        # to_bool_series handles both actual bool dtype and the string
        # "True"/"False" form that round-trips through CSV
        bool_col = to_bool_series(df[col])

        mean_with    = df[bool_col == True]["baseRent"].mean()
        mean_without = df[bool_col == False]["baseRent"].mean()

        rows.append({
            "amenity": label,
            "with":    mean_with,
            "without": mean_without,
            "premium": mean_with - mean_without,
        })

    # Sort by premium descending; reset_index so iterrows() gives 0-based indices
    stats = (
        pd.DataFrame(rows)
        .sort_values("premium", ascending=False)
        .reset_index(drop=True)
    )

    x     = np.arange(len(stats))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(
        x - width / 2,
        stats["with"],
        width,
        color=PRIMARY_BLUE,
        alpha=0.90,
        label="With amenity",
    )
    ax.bar(
        x + width / 2,
        stats["without"],
        width,
        color=NEUTRAL_GREY,
        alpha=0.75,
        label="Without amenity",
    )

    # Premium annotation above each pair
    for i, row in stats.iterrows():
        y_top = max(row["with"], row["without"]) + 25
        sign  = "+" if row["premium"] >= 0 else ""
        ax.text(
            x[i],
            y_top,
            f"{sign}€{row['premium']:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="#C0392B" if row["premium"] >= 0 else "#27AE60",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(stats["amenity"], fontsize=10)
    ax.set_ylabel("Average Monthly Base Rent (€)")
    ax.set_title("Impact of Key Amenities on Average Monthly Rent")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(eur_formatter))
    ax.legend(frameon=True)
    ax.set_ylim(bottom=0)

    footnote(
        ax,
        "Data: ImmobilienScout24 via Kaggle (corrieaar)  —  "
        "shows correlation, not causation",
    )

    plt.tight_layout()
    save_figure(fig, "09_amenity_impact.png")


def chart_10_price_per_sqm_dist_by_bezirk(df: pd.DataFrame) -> None:
    """
    Chart 10 — Price per m² Distribution by Berlin District

    Horizontal box plots of price_per_sqm — one per Bezirk — sorted by
    their median value (highest at the top).

    This is the distribution companion to Chart 03, which showed only
    the mean.  Two districts can have the same average price/m² yet
    very different distributions: one might be uniformly priced; another
    might contain both cheap outer Kieze and expensive central areas,
    producing a wide IQR and many outliers.

    The x-axis is capped at the 99th percentile so the box widths remain
    clearly visible even in districts with long outlier tails.

    Why this chart:
        Closing the loop between Chart 03 (mean) and Chart 10
        (distribution) demonstrates that you don't stop at a single
        summary statistic — you always ask what the distribution looks like.
    """
    print("Chart 10 — Price/m² Distribution by Bezirk (box plot) …")

    # Determine the order of districts by their median price_per_sqm
    median_order = (
        df.groupby("bezirk")["price_per_sqm"]
        .median()
        .sort_values(ascending=True)   # ascending → most expensive at top of horizontal chart
        .index.tolist()
    )
    median_vals = df.groupby("bezirk")["price_per_sqm"].median()

    fig, ax = plt.subplots(figsize=(11, 8))

    sns.boxplot(
        data=df,
        x="price_per_sqm",
        y="bezirk",
        order=median_order,
        color=PRIMARY_BLUE,
        flierprops=dict(
            marker="o",
            markerfacecolor=NEUTRAL_GREY,
            markersize=2.5,
            alpha=0.40,
            linestyle="none",
        ),
        linewidth=0.9,
        ax=ax,
    )

    # Annotate each row with its median value.
    # x_gap is a small proportional offset so the label doesn't start
    # right at the end of the median line.
    x_gap = df["price_per_sqm"].quantile(0.75) * 0.015
    for i, bezirk_name in enumerate(median_order):
        med = median_vals[bezirk_name]
        ax.text(
            med + x_gap,
            i,
            f"€{med:.2f}",
            va="center",
            ha="left",
            fontsize=8.5,
            color="#333333",
        )

    ax.set_xlabel("Price per m² (€/m²)")
    ax.set_ylabel("")   # district names on the y-axis are self-explanatory
    ax.set_title("Rent Price per m² Distribution by Berlin District")
    ax.set_xlim(left=0, right=df["price_per_sqm"].quantile(0.99) * 1.12)

    footnote(ax, "Data: ImmobilienScout24 via Kaggle (corrieaar) — n = 10,369 Berlin listings")

    plt.tight_layout()
    save_figure(fig, "10_price_per_sqm_dist_by_bezirk.png")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """
    Entry point — loads the data once, then runs all ten chart functions.

    Each chart function is called inside a try/except so that a single
    failing chart does not stop the rest from running.  This makes it
    easy to spot and fix individual issues while still getting output
    from all the charts that work correctly.
    """
    print("=" * 62)
    print("  Berlin Rental Market Analyzer — Phase 4 Visualisations")
    print("=" * 62)

    df = load_data()
    print()

    chart_functions = [
        chart_01_avg_rent_by_bezirk,
        chart_02_rent_distribution,
        chart_03_price_per_sqm_by_bezirk,
        chart_04_rent_by_property_type,
        chart_05_area_vs_rent_scatter,
        chart_06_correlation_heatmap,
        chart_07_rent_by_size_category,
        chart_08_rent_by_era,
        chart_09_amenity_impact,
        chart_10_price_per_sqm_dist_by_bezirk,
    ]

    success_count = 0
    for chart_fn in chart_functions:
        try:
            chart_fn(df)
            success_count += 1
        except Exception as exc:
            # Print the error but keep going — other charts are independent
            print(f"\n  ✗  {chart_fn.__name__} failed:")
            print(f"     {type(exc).__name__}: {exc}")

    print()
    print("=" * 62)
    print(f"  Result: {success_count} / {len(chart_functions)} charts saved")
    print(f"  Output: {FIGURES_DIR}/")
    print("=" * 62)


if __name__ == "__main__":
    main()

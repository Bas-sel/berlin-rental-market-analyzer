"""
Phase 1 — Data Acquisition
===========================
Downloads the apartment rental dataset from Kaggle and saves it to data/raw/.

Dataset  : corrieaar/apartment-rental-offers-in-germany
Source   : ImmobilienScout24 scrapes (2018–2019)
Coverage : Germany-wide — Berlin listings filtered in Phase 2

Usage
-----
    python src/download_data.py

Prerequisites
-------------
    pip install kaggle
    Place kaggle.json at C:\\Users\\<username>\\.kaggle\\kaggle.json
"""

import subprocess
import sys
from pathlib import Path


# ── CONFIG ─────────────────────────────────────────────────────────────────────
DATASET_IDENTIFIER = "corrieaar/apartment-rental-offers-in-germany"
RAW_DATA_DIR = Path("../data/raw")
# ───────────────────────────────────────────────────────────────────────────────


def check_kaggle_credentials() -> None:
    """
    Verify that kaggle.json exists before attempting any download.
    Exits with a clear error message if credentials are missing.
    """
    credentials_file = Path.home() / ".kaggle" / "kaggle.json"

    if not credentials_file.exists():
        print("ERROR: kaggle.json not found.")
        print(f"       Expected location: {credentials_file}")
        print()
        print("Fix:")
        print("  1. Go to https://www.kaggle.com/account")
        print("  2. Scroll to API → click 'Create New API Token'")
        print(f"  3. Move the downloaded kaggle.json to: {credentials_file.parent}")
        sys.exit(1)

    print(f"[OK] kaggle.json found at: {credentials_file}")


def check_kaggle_installed() -> None:
    """
    Verify that the kaggle CLI is available on PATH.
    Exits with install instructions if not found.
    """
    result = subprocess.run(
        ["kaggle", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if result.returncode != 0:
        print("ERROR: 'kaggle' command not found.")
        print("       Run: pip install kaggle")
        sys.exit(1)

    print(f"[OK] kaggle CLI detected: {result.stdout.strip()}")


def download_dataset() -> None:
    """
    Download and unzip the dataset from Kaggle into data/raw/.
    Prints the name and size of every file created.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nDownloading: {DATASET_IDENTIFIER}")
    print(f"Destination: {RAW_DATA_DIR.resolve()}")
    print("(This may take a minute — the dataset is ~130 MB compressed)\n")

    result = subprocess.run(
        [
            "kaggle", "datasets", "download",
            "--dataset", DATASET_IDENTIFIER,
            "--path", str(RAW_DATA_DIR),
            "--unzip",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if result.returncode != 0:
        print("ERROR during download:")
        print(result.stderr)
        sys.exit(1)

    print("[OK] Download and unzip complete.\n")
    print("Files now in data/raw/:")
    print(f"  {'Filename':<45} {'Size':>10}")
    print(f"  {'-'*45} {'-'*10}")
    for f in sorted(RAW_DATA_DIR.iterdir()):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:<45} {size_mb:>8.1f} MB")


def print_next_steps() -> None:
    """Print the verification steps to run after download."""
    print()
    print("─" * 60)
    print("NEXT STEPS")
    print("─" * 60)
    print("1. Confirm at least one .csv file is in data/raw/")
    print("2. Open it in a text editor — check that column headers")
    print("   are readable and values look like rental listings")
    print("3. Run the quality check script:")
    print()
    print("   python src/data_quality_check.py data/raw/immo_data.csv")
    print()
    print("4. Paste the full output to Claude for review.")
    print("─" * 60)


if __name__ == "__main__":
    check_kaggle_installed()
    check_kaggle_credentials()
    download_dataset()
    print_next_steps()

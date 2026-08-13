"""
GLOF EWS — Rainfall Processing Pipeline

Purpose:
    Process NASA GPM IMERG precipitation data for
    rainfall accumulation and early-warning analysis.

Planned outputs:
    - 1-hour rainfall accumulation
    - 3-hour rainfall accumulation
    - 6-hour rainfall accumulation
    - 24-hour rainfall accumulation
"""

from pathlib import Path
import pandas as pd


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_IMERG_DIR = PROJECT_ROOT / "data" / "raw" / "imerg"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main():
    print("GLOF EWS rainfall processing pipeline")
    print(f"Raw IMERG directory: {RAW_IMERG_DIR}")
    print(f"Processed directory: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
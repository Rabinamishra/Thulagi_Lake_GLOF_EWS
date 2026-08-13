import argparse
from pathlib import Path

import earthaccess
import xarray as xr
import pandas as pd
import numpy as np


SOURCE = "GPM_IMERG_EarlyRun_V07"
STATION_ID = "IMERG_BASIN_MEAN"


def login():

    auth = earthaccess.login(strategy="netrc")

    if not auth.authenticated:
        raise RuntimeError(
            "NASA Earthdata authentication failed."
        )

    print("NASA Earthdata authentication successful.")


def fetch_data(start, end, bbox):

    south, west, north, east = bbox

    print("Searching NASA IMERG data...")

    results = earthaccess.search_data(
        short_name="GPM_3IMERGHHE",
        temporal=(start, end),
        bounding_box=(west, south, east, north),
    )

    if not results:
        raise RuntimeError(
            "No IMERG data found for the selected period and area."
        )

    print(f"Found {len(results)} IMERG granules.")

    files = earthaccess.open(results)

    return files


def process_data(files, bbox):

    south, west, north, east = bbox

    rows = []

    for i, file in enumerate(files):

        print(f"Processing {i + 1}/{len(files)}")

        ds = xr.open_dataset(
            file,
            group="Grid"
        )

        rainfall = ds["precipitation"].sel(
            lat=slice(south, north),
            lon=slice(west, east)
        )

        mean_rate = float(
            rainfall.mean(skipna=True).values
        )

        timestamp = pd.to_datetime(
            ds["time"].values[0]
        )

        rainfall_mm = mean_rate * 0.5

        rows.append({
            "timestamp": timestamp,
            "rainfall_mm": rainfall_mm
        })

        ds.close()

    df = pd.DataFrame(rows)

    df = df.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    return df


def quality_control(df):

    df = df.copy()

    df["quality_flag"] = "ok"

    df.loc[
        df["rainfall_mm"].isna(),
        "quality_flag"
    ] = "missing"

    df.loc[
        df["rainfall_mm"] < 0,
        "quality_flag"
    ] = "negative_value"

    df.loc[
        df["rainfall_mm"] > 100,
        "quality_flag"
    ] = "spike_review"

    df["rainfall_clean_mm"] = (
        df["rainfall_mm"]
        .fillna(0)
        .clip(lower=0)
    )

    return df


def calculate_accumulations(df):

    df = df.copy()

    df = df.set_index(
        "timestamp"
    )

    full_index = pd.date_range(
        df.index.min(),
        df.index.max(),
        freq="30min"
    )

    df = df.reindex(full_index)

    df.index.name = "timestamp"

    df["quality_flag"] = (
        df["quality_flag"]
        .fillna("missing")
    )

    df["rainfall_clean_mm"] = (
        df["rainfall_clean_mm"]
        .fillna(0)
    )

    df["rainfall_1h_mm"] = (
        df["rainfall_clean_mm"]
        .rolling(2, min_periods=1)
        .sum()
    )

    df["rainfall_3h_mm"] = (
        df["rainfall_clean_mm"]
        .rolling(6, min_periods=1)
        .sum()
    )

    df["rainfall_6h_mm"] = (
        df["rainfall_clean_mm"]
        .rolling(12, min_periods=1)
        .sum()
    )

    df["rainfall_24h_mm"] = (
        df["rainfall_clean_mm"]
        .rolling(48, min_periods=1)
        .sum()
    )

    df = df.reset_index()

    return df


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        required=True
    )

    parser.add_argument(
        "--end",
        required=True
    )

    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True
    )

    parser.add_argument(
        "--out",
        default="real_observations.csv"
    )

    args = parser.parse_args()

    bbox = tuple(args.bbox)

    print()
    print("=== NASA IMERG REAL-DATA PIPELINE ===")
    print()

    login()

    files = fetch_data(
        args.start,
        args.end,
        bbox
    )

    df = process_data(
        files,
        bbox
    )

    df = quality_control(df)

    df = calculate_accumulations(df)

    df["station_id"] = STATION_ID
    df["source"] = SOURCE

    final = df[
        [
            "timestamp",
            "station_id",
            "rainfall_mm",
            "rainfall_1h_mm",
            "rainfall_3h_mm",
            "rainfall_6h_mm",
            "rainfall_24h_mm",
            "quality_flag",
            "source"
        ]
    ]

    output = Path(args.out)

    final.to_csv(
        output,
        index=False
    )

    print()
    print("SUCCESS")
    print(f"Saved {len(final)} observations")
    print(f"Output: {output}")
    print()
    print(final.head())


if __name__ == "__main__":
    main()
from pathlib import Path
import argparse

import numpy as np
import rasterio
from rasterio.enums import Resampling


# =========================================================
# CONFIGURATION
# =========================================================

BASE = Path("data/processed/sentinel2")
INDEX_DIR = BASE / "indices"
OUTPUT_DIR = INDEX_DIR / "masked"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# FIND CLASSIFICATION MASK
# =========================================================

def find_mask(date):
    date_dir = BASE / date

    matches = list(
        date_dir.glob(
            "**/GRANULE/*/QI_DATA/MSK_CLASSI_B00.jp2"
        )
    )

    if not matches:
        raise FileNotFoundError(
            f"MSK_CLASSI_B00.jp2 not found for {date}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple MSK_CLASSI_B00.jp2 files found for {date}"
        )

    return matches[0]


# =========================================================
# FIND NDWI / MNDWI FILE
# =========================================================

def find_index_file(date, index_name):

    date_compact = date.replace("_", "")

    matches = list(
        INDEX_DIR.glob(
            f"S2?_{date_compact}_{index_name}_TOA.tif"
        )
    )

    if not matches:
        raise FileNotFoundError(
            f"{index_name} file not found for {date}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple {index_name} files found for {date}: "
            f"{matches}"
        )

    return matches[0]


# =========================================================
# READ AND RESAMPLE CLASSIFICATION MASK
# =========================================================

def create_cloud_mask(mask_file, height, width):

    with rasterio.open(mask_file) as src:

        if src.count != 3:
            raise RuntimeError(
                f"Expected 3 MSK_CLASSI bands, "
                f"found {src.count}"
            )

        opaque_cloud = src.read(
            1,
            out_shape=(height, width),
            resampling=Resampling.nearest
        )

        cirrus = src.read(
            2,
            out_shape=(height, width),
            resampling=Resampling.nearest
        )

        snow_ice = src.read(
            3,
            out_shape=(height, width),
            resampling=Resampling.nearest
        )

    cloud_mask = (
        (opaque_cloud == 1)
        | (cirrus == 1)
        | (snow_ice == 1)
    )

    return cloud_mask


# =========================================================
# PROCESS ONE SENTINEL-2 SCENE
# =========================================================

def process_scene(date):

    print("\n" + "=" * 60)
    print(f"PROCESSING SENTINEL-2 SCENE: {date}")
    print("=" * 60)

    # -----------------------------------------------------
    # FIND INPUT FILES
    # -----------------------------------------------------

    mask_file = find_mask(date)

    ndwi_file = find_index_file(
        date,
        "NDWI"
    )

    mndwi_file = find_index_file(
        date,
        "MNDWI"
    )

    print("\nMask:")
    print(mask_file)

    print("\nNDWI:")
    print(ndwi_file)

    print("\nMNDWI:")
    print(mndwi_file)

    # -----------------------------------------------------
    # READ NDWI
    # -----------------------------------------------------

    with rasterio.open(ndwi_file) as src:

        ndwi = src.read(1).astype("float32")

        profile = src.profile.copy()

        width = src.width
        height = src.height

        transform = src.transform
        crs = src.crs

    # -----------------------------------------------------
    # READ MNDWI
    # -----------------------------------------------------

    with rasterio.open(mndwi_file) as src:

        mndwi = src.read(1).astype("float32")

        if src.width != width or src.height != height:
            raise RuntimeError(
                f"{date}: NDWI and MNDWI dimensions "
                f"do not match."
            )

        if src.transform != transform:
            raise RuntimeError(
                f"{date}: NDWI and MNDWI transforms "
                f"do not match."
            )

        if src.crs != crs:
            raise RuntimeError(
                f"{date}: NDWI and MNDWI CRS "
                f"do not match."
            )

    # -----------------------------------------------------
    # CREATE CLOUD / SNOW MASK
    # -----------------------------------------------------

    cloud_mask = create_cloud_mask(
        mask_file,
        height,
        width
    )

    # -----------------------------------------------------
    # APPLY MASK
    # -----------------------------------------------------

    ndwi_masked = ndwi.copy()
    mndwi_masked = mndwi.copy()

    ndwi_masked[cloud_mask] = np.nan
    mndwi_masked[cloud_mask] = np.nan

    # -----------------------------------------------------
    # OUTPUT PROFILE
    # -----------------------------------------------------

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        compress="deflate",
        predictor=2,
        nodata=np.nan
    )

    # -----------------------------------------------------
    # DETERMINE SENTINEL PLATFORM
    # -----------------------------------------------------

    platform = ndwi_file.name.split("_")[0]

    # -----------------------------------------------------
    # OUTPUT FILES
    # -----------------------------------------------------

    date_compact = date.replace("_", "")

    ndwi_out = (
        OUTPUT_DIR
        / f"{platform}_{date_compact}_NDWI_TOA_MASKED.tif"
    )

    mndwi_out = (
        OUTPUT_DIR
        / f"{platform}_{date_compact}_MNDWI_TOA_MASKED.tif"
    )

    # -----------------------------------------------------
    # WRITE NDWI
    # -----------------------------------------------------

    with rasterio.open(
        ndwi_out,
        "w",
        **profile
    ) as dst:

        dst.write(
            ndwi_masked,
            1
        )

    # -----------------------------------------------------
    # WRITE MNDWI
    # -----------------------------------------------------

    with rasterio.open(
        mndwi_out,
        "w",
        **profile
    ) as dst:

        dst.write(
            mndwi_masked,
            1
        )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    total_pixels = height * width

    masked_pixels = int(
        np.count_nonzero(cloud_mask)
    )

    clear_pixels = (
        total_pixels - masked_pixels
    )

    masked_percentage = (
        masked_pixels / total_pixels * 100
    )

    print("\nValidation:")
    print(f"Platform: {platform}")
    print(f"Grid: {width} x {height}")
    print(f"Total pixels: {total_pixels:,}")
    print(f"Masked pixels: {masked_pixels:,}")
    print(f"Clear pixels: {clear_pixels:,}")
    print(
        f"Masked percentage: "
        f"{masked_percentage:.4f}%"
    )

    print("\nOutputs:")
    print(ndwi_out)
    print(mndwi_out)

    print("\nSTATUS: SUCCESS")


# =========================================================
# COMMAND-LINE INTERFACE
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Apply Sentinel-2 cloud, cirrus, "
            "and snow/ice masking to NDWI/MNDWI."
        )
    )

    parser.add_argument(
        "--date",
        help="Process one scene, e.g. 2025_12_30"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all available Sentinel-2 scenes"
    )

    args = parser.parse_args()

    if not args.date and not args.all:
        parser.error(
            "Specify either --date DATE or --all"
        )

    if args.date:
        process_scene(args.date)

    if args.all:

        dates = sorted(
            p.name
            for p in BASE.iterdir()
            if p.is_dir()
            and "_" in p.name
            and len(p.name) == 10
        )

        for date in dates:
            process_scene(date)


if __name__ == "__main__":
    main()
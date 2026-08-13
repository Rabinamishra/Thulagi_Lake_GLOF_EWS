from pathlib import Path

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

DATES = [
    "2018_11_22",
    "2020_12_31",
    "2022_12_31",
    "2024_12_20",
]


# =========================================================
# FIND SENTINEL-2 CLASSIFICATION MASK
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
# FIND NDWI / MNDWI
# =========================================================

def find_index_file(date, index_name):

    date_compact = date.replace("_", "")

    filename = (
        f"S2A_{date_compact}_{index_name}_TOA.tif"
    )

    path = INDEX_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required index file not found: {path}"
        )

    return path


# =========================================================
# PROCESS ONE SCENE
# =========================================================

def process_scene(date):

    print("\n" + "=" * 58)
    print(f"PROCESSING {date}")
    print("=" * 58)

    # -----------------------------------------------------
    # LOCATE FILES
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
                f"{date}: NDWI and MNDWI dimensions do not match."
            )

        if src.transform != transform:
            raise RuntimeError(
                f"{date}: NDWI and MNDWI transforms do not match."
            )

        if src.crs != crs:
            raise RuntimeError(
                f"{date}: NDWI and MNDWI CRS do not match."
            )

    # -----------------------------------------------------
    # READ MSK_CLASSI
    #
    # MSK_CLASSI_B00 has 3 bands:
    #
    # Band 1 = opaque cloud
    # Band 2 = cirrus
    # Band 3 = snow / ice
    #
    # Source resolution = 60 m
    # Target resolution = 10 m
    #
    # Nearest-neighbour is used because the masks
    # contain categorical values.
    # -----------------------------------------------------

    with rasterio.open(mask_file) as src:

        if src.count != 3:
            raise RuntimeError(
                f"{date}: Expected 3 MSK_CLASSI bands, "
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

        print("\nMask information:")
        print(f"Mask bands: {src.count}")
        print(
            f"Mask source grid: "
            f"{src.width} x {src.height}"
        )
        print(f"Mask dtype: {opaque_cloud.dtype}")

        print(
            "Opaque cloud values:",
            np.unique(opaque_cloud)
        )

        print(
            "Cirrus values:",
            np.unique(cirrus)
        )

        print(
            "Snow/ice values:",
            np.unique(snow_ice)
        )

    # -----------------------------------------------------
    # CREATE VALID PIXEL MASK
    #
    # 0 = clear
    # 1 = flagged
    # -----------------------------------------------------

    cloud_mask = (
        (opaque_cloud == 1)
        | (cirrus == 1)
        | (snow_ice == 1)
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
    # OUTPUT FILES
    # -----------------------------------------------------

    ndwi_out = (
        OUTPUT_DIR
        / f"S2A_{date.replace('_', '')}_NDWI_TOA_MASKED.tif"
    )

    mndwi_out = (
        OUTPUT_DIR
        / f"S2A_{date.replace('_', '')}_MNDWI_TOA_MASKED.tif"
    )

    # -----------------------------------------------------
    # WRITE MASKED NDWI
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
    # WRITE MASKED MNDWI
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

    print("\nValidation:")
    print(f"Grid: {width} x {height}")
    print(f"Total pixels: {total_pixels:,}")
    print(f"Masked pixels: {masked_pixels:,}")
    print(f"Clear pixels: {clear_pixels:,}")

    print(
        f"Masked percentage: "
        f"{masked_pixels / total_pixels * 100:.4f}%"
    )

    print("\nOutputs:")
    print(ndwi_out)
    print(mndwi_out)

    print("\nSTATUS: SUCCESS")


# =========================================================
# MAIN
# =========================================================

print("\n" + "=" * 58)
print("SENTINEL-2 NDWI / MNDWI CLOUD MASKING")
print("=" * 58)

for date in DATES:
    process_scene(date)

print("\n" + "=" * 58)
print("ALL FOUR SCENES MASKED SUCCESSFULLY")
print("=" * 58)
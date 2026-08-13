from pathlib import Path
import re

import numpy as np
import rasterio
from rasterio.enums import Resampling


# =========================================================
# CONFIGURATION
# =========================================================

SCENES = {
    "2018_11_22": "S2A",
    "2020_12_31": "S2A",
    "2022_12_31": "S2A",
    "2024_12_20": "S2A",
}

BASE = Path("data/processed/sentinel2")
OUTPUT = BASE / "indices"
OUTPUT.mkdir(parents=True, exist_ok=True)


# =========================================================
# FIND SAFE PRODUCT
# =========================================================

def find_safe(scene_dir):
    matches = list(scene_dir.glob("*.SAFE"))

    if not matches:
        raise FileNotFoundError(
            f"No SAFE product found in {scene_dir}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple SAFE products found in {scene_dir}: {matches}"
        )

    return matches[0]


# =========================================================
# FIND BAND
# =========================================================

def find_band(img_dir, band):
    matches = list(img_dir.glob(f"*_{band}.jp2"))

    if not matches:
        raise FileNotFoundError(
            f"Could not find {band} in {img_dir}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple {band} files found: {matches}"
        )

    return matches[0]


# =========================================================
# PROCESS ONE SCENE
# =========================================================

def process_scene(date_name, satellite):

    print("\n" + "=" * 50)
    print(f"PROCESSING {date_name}")
    print("=" * 50)

    scene_dir = BASE / date_name
    safe = find_safe(scene_dir)

    granules = list(safe.glob("GRANULE/*"))

    if len(granules) != 1:
        raise RuntimeError(
            f"Expected exactly one GRANULE in {safe}, "
            f"found {len(granules)}"
        )

    granule = granules[0]
    img_dir = granule / "IMG_DATA"
    metadata = safe / "MTD_MSIL1C.xml"

    # -----------------------------------------------------
    # READ METADATA
    # -----------------------------------------------------

    metadata_text = metadata.read_text(encoding="utf-8")

    quant_match = re.search(
        r"<QUANTIFICATION_VALUE[^>]*>([-+0-9.]+)</QUANTIFICATION_VALUE>",
        metadata_text
    )

    offset_match = re.search(
        r'<RADIO_ADD_OFFSET[^>]*band_id="2"[^>]*>([-+0-9.]+)</RADIO_ADD_OFFSET>',
        metadata_text
    )

    if quant_match is None:
        raise RuntimeError(
            f"QUANTIFICATION_VALUE not found for {date_name}"
        )

    if offset_match is None:
        raise RuntimeError(
            f"RADIO_ADD_OFFSET for B03 not found for {date_name}"
        )

    quantification = float(quant_match.group(1))
    radio_offset = float(offset_match.group(1))

    print(f"Scene: {safe.name}")
    print(f"Quantification value: {quantification}")
    print(f"Radio add offset: {radio_offset}")

    # -----------------------------------------------------
    # FIND BANDS
    # -----------------------------------------------------

    B03 = find_band(img_dir, "B03")
    B08 = find_band(img_dir, "B08")
    B11 = find_band(img_dir, "B11")

    print("\nRequired bands:")
    print("B03:", B03.name)
    print("B08:", B08.name)
    print("B11:", B11.name)

    # -----------------------------------------------------
    # READ B03
    # -----------------------------------------------------

    with rasterio.open(B03) as src:

        green_dn = src.read(1).astype("float32")

        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs

        height = src.height
        width = src.width

    # -----------------------------------------------------
    # READ B08
    # -----------------------------------------------------

    with rasterio.open(B08) as src:

        nir_dn = src.read(1).astype("float32")

        if src.width != width or src.height != height:
            raise RuntimeError(
                f"B03 and B08 dimensions do not match for {date_name}"
            )

        if src.transform != transform:
            raise RuntimeError(
                f"B03 and B08 grids do not match for {date_name}"
            )

    # -----------------------------------------------------
    # READ B11 AND RESAMPLE TO 10 m
    # -----------------------------------------------------

    with rasterio.open(B11) as src:

        swir_dn = src.read(
            1,
            out_shape=(height, width),
            resampling=Resampling.bilinear
        ).astype("float32")

    # -----------------------------------------------------
    # DN → TOA REFLECTANCE
    # -----------------------------------------------------

    green = (
        green_dn + radio_offset
    ) / quantification

    nir = (
        nir_dn + radio_offset
    ) / quantification

    swir = (
        swir_dn + radio_offset
    ) / quantification

    # -----------------------------------------------------
    # VALID PIXELS
    # -----------------------------------------------------

    valid = (
        np.isfinite(green)
        & np.isfinite(nir)
        & np.isfinite(swir)
        & (green >= 0)
        & (nir >= 0)
        & (swir >= 0)
    )

    # -----------------------------------------------------
    # NDWI
    # -----------------------------------------------------

    ndwi_denominator = green + nir

    ndwi = np.full(
        green.shape,
        np.nan,
        dtype="float32"
    )

    ndwi_valid = (
        valid
        & (ndwi_denominator != 0)
    )

    ndwi[ndwi_valid] = (
        (green[ndwi_valid] - nir[ndwi_valid])
        / ndwi_denominator[ndwi_valid]
    )

    # -----------------------------------------------------
    # MNDWI
    # -----------------------------------------------------

    mndwi_denominator = green + swir

    mndwi = np.full(
        green.shape,
        np.nan,
        dtype="float32"
    )

    mndwi_valid = (
        valid
        & (mndwi_denominator != 0)
    )

    mndwi[mndwi_valid] = (
        (green[mndwi_valid] - swir[mndwi_valid])
        / mndwi_denominator[mndwi_valid]
    )

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

    ndwi_file = (
        OUTPUT /
        f"{satellite}_{date_name.replace('_', '')}_NDWI_TOA.tif"
    )

    mndwi_file = (
        OUTPUT /
        f"{satellite}_{date_name.replace('_', '')}_MNDWI_TOA.tif"
    )

    # -----------------------------------------------------
    # WRITE NDWI
    # -----------------------------------------------------

    with rasterio.open(
        ndwi_file,
        "w",
        **profile
    ) as dst:

        dst.write(ndwi, 1)

    # -----------------------------------------------------
    # WRITE MNDWI
    # -----------------------------------------------------

    with rasterio.open(
        mndwi_file,
        "w",
        **profile
    ) as dst:

        dst.write(mndwi, 1)

    # -----------------------------------------------------
    # VALIDATION STATISTICS
    # -----------------------------------------------------

    ndwi_values = ndwi[np.isfinite(ndwi)]
    mndwi_values = mndwi[np.isfinite(mndwi)]

    print("\nNDWI statistics:")
    print(f"Minimum: {np.min(ndwi_values):.4f}")
    print(f"Maximum: {np.max(ndwi_values):.4f}")
    print(f"Mean:    {np.mean(ndwi_values):.4f}")

    print("\nMNDWI statistics:")
    print(f"Minimum: {np.min(mndwi_values):.4f}")
    print(f"Maximum: {np.max(mndwi_values):.4f}")
    print(f"Mean:    {np.mean(mndwi_values):.4f}")

    print("\nOutputs:")
    print(ndwi_file)
    print(mndwi_file)


# =========================================================
# RUN ALL FOUR YEARS
# =========================================================

for date_name, satellite in SCENES.items():
    process_scene(date_name, satellite)

print("\n" + "=" * 50)
print("ALL FOUR SCENES PROCESSED SUCCESSFULLY")
print("=" * 50)
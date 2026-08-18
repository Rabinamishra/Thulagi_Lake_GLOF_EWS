from pathlib import Path
import argparse
import re

import numpy as np
import rasterio
from rasterio.enums import Resampling


# =========================================================
# CONFIGURATION
# =========================================================

BASE = Path("data/processed/sentinel2")
OUTPUT = BASE / "indices"
OUTPUT.mkdir(parents=True, exist_ok=True)


# =========================================================
# FIND SENTINEL-2 SAFE PRODUCT
# =========================================================

def find_safe(scene_dir):

    matches = list(scene_dir.glob("*.SAFE"))

    if not matches:
        raise FileNotFoundError(
            f"No SAFE product found in {scene_dir}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple SAFE products found in {scene_dir}: "
            f"{matches}"
        )

    return matches[0]


# =========================================================
# FIND BAND
# =========================================================

def find_band(img_dir, band):

    matches = list(
        img_dir.glob(f"*_{band}.jp2")
    )

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
# DETECT SATELLITE PLATFORM
# =========================================================

def detect_satellite(safe):

    name = safe.name

    if name.startswith("S2A_"):
        return "S2A"

    if name.startswith("S2B_"):
        return "S2B"

    raise RuntimeError(
        f"Could not determine Sentinel-2 platform from "
        f"SAFE name: {name}"
    )


# =========================================================
# READ RADIOMETRIC METADATA
# =========================================================

def read_radiometric_metadata(metadata):

    metadata_text = metadata.read_text(
        encoding="utf-8"
    )

    quant_match = re.search(
        r"<QUANTIFICATION_VALUE[^>]*>"
        r"([-+0-9.]+)"
        r"</QUANTIFICATION_VALUE>",
        metadata_text
    )

    offset_match = re.search(
        r'<RADIO_ADD_OFFSET[^>]*band_id="2"[^>]*>'
        r"([-+0-9.]+)"
        r"</RADIO_ADD_OFFSET>",
        metadata_text
    )

    if quant_match is None:
        raise RuntimeError(
            "QUANTIFICATION_VALUE not found in "
            "MTD_MSIL1C.xml"
        )

    if offset_match is None:
        raise RuntimeError(
            "RADIO_ADD_OFFSET for B03 not found in "
            "MTD_MSIL1C.xml"
        )

    quantification = float(
        quant_match.group(1)
    )

    radio_offset = float(
        offset_match.group(1)
    )

    return quantification, radio_offset


# =========================================================
# PROCESS ONE SCENE
# =========================================================

def process_scene(date):

    print("\n" + "=" * 60)
    print(
        f"PROCESSING SENTINEL-2 SCENE: {date}"
    )
    print("=" * 60)

    scene_dir = BASE / date

    if not scene_dir.exists():
        raise FileNotFoundError(
            f"Scene directory not found: {scene_dir}"
        )

    # -----------------------------------------------------
    # FIND SAFE PRODUCT
    # -----------------------------------------------------

    safe = find_safe(scene_dir)

    satellite = detect_satellite(safe)

    granules = list(
        safe.glob("GRANULE/*")
    )

    if len(granules) != 1:
        raise RuntimeError(
            f"Expected exactly one GRANULE in {safe}, "
            f"found {len(granules)}"
        )

    granule = granules[0]

    img_dir = granule / "IMG_DATA"
    metadata = safe / "MTD_MSIL1C.xml"

    if not metadata.exists():
        raise FileNotFoundError(
            f"Metadata not found: {metadata}"
        )

    # -----------------------------------------------------
    # READ RADIOMETRIC METADATA
    # -----------------------------------------------------

    quantification, radio_offset = (
        read_radiometric_metadata(metadata)
    )

    print(f"Satellite: {satellite}")
    print(f"Scene: {safe.name}")
    print(
        f"Quantification value: "
        f"{quantification}"
    )
    print(
        f"Radio add offset: "
        f"{radio_offset}"
    )

    # -----------------------------------------------------
    # FIND REQUIRED BANDS
    # -----------------------------------------------------

    b03 = find_band(img_dir, "B03")
    b08 = find_band(img_dir, "B08")
    b11 = find_band(img_dir, "B11")

    print("\nRequired bands:")
    print("B03:", b03.name)
    print("B08:", b08.name)
    print("B11:", b11.name)

    # -----------------------------------------------------
    # READ B03 — GREEN, 10 m
    # -----------------------------------------------------

    with rasterio.open(b03) as src:

        green_dn = src.read(
            1
        ).astype("float32")

        profile = src.profile.copy()

        transform = src.transform
        crs = src.crs

        height = src.height
        width = src.width

    # -----------------------------------------------------
    # READ B08 — NIR, 10 m
    # -----------------------------------------------------

    with rasterio.open(b08) as src:

        nir_dn = src.read(
            1
        ).astype("float32")

        if (
            src.width != width
            or src.height != height
        ):
            raise RuntimeError(
                f"B03 and B08 dimensions do not "
                f"match for {date}"
            )

        if src.transform != transform:
            raise RuntimeError(
                f"B03 and B08 grids do not "
                f"match for {date}"
            )

        if src.crs != crs:
            raise RuntimeError(
                f"B03 and B08 CRS do not "
                f"match for {date}"
            )

    # -----------------------------------------------------
    # READ B11 — SWIR, 20 m
    # RESAMPLE TO 10 m GRID
    # -----------------------------------------------------

    with rasterio.open(b11) as src:

        swir_dn = src.read(
            1,
            out_shape=(height, width),
            resampling=Resampling.bilinear
        ).astype("float32")

    # -----------------------------------------------------
    # DN → TOA REFLECTANCE
    #
    # TOA =
    # (DN + RADIO_ADD_OFFSET)
    # / QUANTIFICATION_VALUE
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
    #
    # NDWI = (Green - NIR)
    #        / (Green + NIR)
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
        (
            green[ndwi_valid]
            - nir[ndwi_valid]
        )
        /
        ndwi_denominator[ndwi_valid]
    )

    # -----------------------------------------------------
    # MNDWI
    #
    # MNDWI = (Green - SWIR)
    #         / (Green + SWIR)
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
        (
            green[mndwi_valid]
            - swir[mndwi_valid]
        )
        /
        mndwi_denominator[mndwi_valid]
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

    date_compact = date.replace(
        "_", ""
    )

    ndwi_file = (
        OUTPUT
        / f"{satellite}_{date_compact}_"
        "NDWI_TOA.tif"
    )

    mndwi_file = (
        OUTPUT
        / f"{satellite}_{date_compact}_"
        "MNDWI_TOA.tif"
    )

    # -----------------------------------------------------
    # WRITE NDWI
    # -----------------------------------------------------

    with rasterio.open(
        ndwi_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            ndwi,
            1
        )

    # -----------------------------------------------------
    # WRITE MNDWI
    # -----------------------------------------------------

    with rasterio.open(
        mndwi_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            mndwi,
            1
        )

    # -----------------------------------------------------
    # VALIDATION STATISTICS
    # -----------------------------------------------------

    ndwi_values = ndwi[
        np.isfinite(ndwi)
    ]

    mndwi_values = mndwi[
        np.isfinite(mndwi)
    ]

    print("\nGrid:")
    print(
        f"{width} x {height}"
    )

    print("\nNDWI statistics:")
    print(
        f"Minimum: "
        f"{np.min(ndwi_values):.4f}"
    )
    print(
        f"Maximum: "
        f"{np.max(ndwi_values):.4f}"
    )
    print(
        f"Mean:    "
        f"{np.mean(ndwi_values):.4f}"
    )

    print("\nMNDWI statistics:")
    print(
        f"Minimum: "
        f"{np.min(mndwi_values):.4f}"
    )
    print(
        f"Maximum: "
        f"{np.max(mndwi_values):.4f}"
    )
    print(
        f"Mean:    "
        f"{np.mean(mndwi_values):.4f}"
    )

    print("\nOutputs:")
    print(ndwi_file)
    print(mndwi_file)

    print("\nSTATUS: SUCCESS")


# =========================================================
# COMMAND-LINE INTERFACE
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Calculate Sentinel-2 "
            "NDWI and MNDWI."
        )
    )

    parser.add_argument(
        "--date",
        required=True,
        help=(
            "Scene date, e.g. "
            "2025_12_30"
        )
    )

    args = parser.parse_args()

    process_scene(args.date)


if __name__ == "__main__":
    main()
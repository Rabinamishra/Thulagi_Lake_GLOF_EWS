from pathlib import Path
import re

import numpy as np
import rasterio
from rasterio.enums import Resampling


# =========================================================
# CONFIGURATION
# =========================================================

BASE = Path("data/processed/sentinel2/2016_11_02")

SAFE = next(BASE.glob("*.SAFE"))
GRANULE = next(SAFE.glob("GRANULE/*"))
IMG = GRANULE / "IMG_DATA"

METADATA = SAFE / "MTD_MSIL1C.xml"

OUTPUT = Path("data/processed/sentinel2/indices")
OUTPUT.mkdir(parents=True, exist_ok=True)


# =========================================================
# READ SENTINEL-2 L1C RADIOMETRIC METADATA
# =========================================================

metadata_text = METADATA.read_text(encoding="utf-8")

quant_match = re.search(
    r"<QUANTIFICATION_VALUE[^>]*>([-+0-9.]+)</QUANTIFICATION_VALUE>",
    metadata_text
)

offset_match = re.search(
    r'<RADIO_ADD_OFFSET[^>]*band_id="2"[^>]*>([-+0-9.]+)</RADIO_ADD_OFFSET>',
    metadata_text
)

if quant_match is None:
    raise RuntimeError("QUANTIFICATION_VALUE not found in MTD_MSIL1C.xml")

if offset_match is None:
    raise RuntimeError("RADIO_ADD_OFFSET for B03 not found in MTD_MSIL1C.xml")

QUANTIFICATION_VALUE = float(quant_match.group(1))
RADIO_ADD_OFFSET = float(offset_match.group(1))

print("Sentinel-2 L1C radiometric metadata:")
print(f"Quantification value: {QUANTIFICATION_VALUE}")
print(f"Radio add offset:    {RADIO_ADD_OFFSET}")


# =========================================================
# FIND REQUIRED BANDS
# =========================================================

def find_band(band):
    matches = list(IMG.glob(f"*_{band}.jp2"))

    if not matches:
        raise FileNotFoundError(f"Could not find {band}")

    if len(matches) > 1:
        raise RuntimeError(f"Multiple files found for {band}")

    return matches[0]


B03 = find_band("B03")   # Green, 10 m
B08 = find_band("B08")   # NIR, 10 m
B11 = find_band("B11")   # SWIR, 20 m


print("\nRequired bands:")
print("B03:", B03.name)
print("B08:", B08.name)
print("B11:", B11.name)


# =========================================================
# READ B03 — GREEN, 10 m
# =========================================================

with rasterio.open(B03) as src:

    green_dn = src.read(1).astype("float32")

    profile = src.profile.copy()
    transform = src.transform
    crs = src.crs

    height = src.height
    width = src.width

    green_nodata = src.nodata


# =========================================================
# READ B08 — NIR, 10 m
# =========================================================

with rasterio.open(B08) as src:

    nir_dn = src.read(1).astype("float32")

    if src.width != width or src.height != height:
        raise RuntimeError("B03 and B08 do not have matching dimensions.")

    if src.transform != transform:
        raise RuntimeError("B03 and B08 do not share the same grid.")


# =========================================================
# READ B11 — SWIR, 20 m
# =========================================================

with rasterio.open(B11) as src:

    swir_dn = src.read(
        1,
        out_shape=(height, width),
        resampling=Resampling.bilinear
    ).astype("float32")


# =========================================================
# CONVERT L1C DIGITAL NUMBERS → TOA REFLECTANCE
#
# Sentinel-2 L1C:
#
# TOA reflectance =
# (DN + RADIO_ADD_OFFSET) / QUANTIFICATION_VALUE
#
# For this scene:
#
# (DN - 1000) / 10000
# =========================================================

green = (
    green_dn + RADIO_ADD_OFFSET
) / QUANTIFICATION_VALUE

nir = (
    nir_dn + RADIO_ADD_OFFSET
) / QUANTIFICATION_VALUE

swir = (
    swir_dn + RADIO_ADD_OFFSET
) / QUANTIFICATION_VALUE


# =========================================================
# MASK INVALID VALUES
# =========================================================

valid = (
    np.isfinite(green)
    & np.isfinite(nir)
    & np.isfinite(swir)
    & (green >= 0)
    & (nir >= 0)
    & (swir >= 0)
)


# =========================================================
# NDWI
#
# NDWI = (Green - NIR) / (Green + NIR)
# =========================================================

ndwi_denominator = green + nir

ndwi = np.full(
    green.shape,
    np.nan,
    dtype="float32"
)

ndwi_valid = valid & (ndwi_denominator != 0)

ndwi[ndwi_valid] = (
    (green[ndwi_valid] - nir[ndwi_valid])
    / ndwi_denominator[ndwi_valid]
)


# =========================================================
# MNDWI
#
# MNDWI = (Green - SWIR) / (Green + SWIR)
#
# B11 has been resampled to the B03 10 m grid.
# =========================================================

mndwi_denominator = green + swir

mndwi = np.full(
    green.shape,
    np.nan,
    dtype="float32"
)

mndwi_valid = valid & (mndwi_denominator != 0)

mndwi[mndwi_valid] = (
    (green[mndwi_valid] - swir[mndwi_valid])
    / mndwi_denominator[mndwi_valid]
)


# =========================================================
# OUTPUT PROFILE
# =========================================================

profile.update(
    driver="GTiff",
    dtype="float32",
    count=1,
    compress="deflate",
    predictor=2,
    nodata=np.nan
)


# =========================================================
# WRITE NDWI
# =========================================================

ndwi_file = OUTPUT / "S2A_20161102_NDWI_TOA.tif"

with rasterio.open(ndwi_file, "w", **profile) as dst:
    dst.write(ndwi, 1)


# =========================================================
# WRITE MNDWI
# =========================================================

mndwi_file = OUTPUT / "S2A_20161102_MNDWI_TOA.tif"

with rasterio.open(mndwi_file, "w", **profile) as dst:
    dst.write(mndwi, 1)


# =========================================================
# VALIDATION SUMMARY
# =========================================================

ndwi_values = ndwi[np.isfinite(ndwi)]
mndwi_values = mndwi[np.isfinite(mndwi)]

print("\n========================================")
print("PROCESSING COMPLETE")
print("========================================")

print("\nScene:")
print(SAFE.name)

print("\nRadiometric correction:")
print(f"DN + ({RADIO_ADD_OFFSET}) / {QUANTIFICATION_VALUE}")

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
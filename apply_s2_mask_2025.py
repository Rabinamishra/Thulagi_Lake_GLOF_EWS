from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling


# ============================================================
# CONFIGURATION
# ============================================================

BASE = Path(
    "data/processed/sentinel2/2025_12_30"
)

SAFE = next(BASE.glob("*.SAFE"))
GRANULE = next(SAFE.glob("GRANULE/*"))
QI_DATA = GRANULE / "QI_DATA"

MASK_FILE = QI_DATA / "MSK_CLASSI_B00.jp2"

NDWI_FILE = Path(
    "data/processed/sentinel2/indices/"
    "S2B_20251230_NDWI_TOA.tif"
)

MNDWI_FILE = Path(
    "data/processed/sentinel2/indices/"
    "S2B_20251230_MNDWI_TOA.tif"
)

OUTPUT = Path(
    "data/processed/sentinel2/indices/masked"
)

OUTPUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# VERIFY INPUTS
# ============================================================

if not MASK_FILE.exists():
    raise FileNotFoundError(
        f"Classification mask not found:\n{MASK_FILE}"
    )

if not NDWI_FILE.exists():
    raise FileNotFoundError(
        f"NDWI file not found:\n{NDWI_FILE}"
    )

if not MNDWI_FILE.exists():
    raise FileNotFoundError(
        f"MNDWI file not found:\n{MNDWI_FILE}"
    )


print("========================================")
print("2025 SENTINEL-2 MASKING")
print("========================================")

print("\nScene:")
print(SAFE.name)

print("\nClassification mask:")
print(MASK_FILE)


# ============================================================
# READ CLASSIFICATION MASK
# ============================================================

with rasterio.open(MASK_FILE) as src:

    opaque_cloud = src.read(
        1,
        out_shape=(10980, 10980),
        resampling=Resampling.nearest
    )

    cirrus = src.read(
        2,
        out_shape=(10980, 10980),
        resampling=Resampling.nearest
    )

    snow_ice = src.read(
        3,
        out_shape=(10980, 10980),
        resampling=Resampling.nearest
    )


# ============================================================
# CREATE INVALID-PIXEL MASK
#
# Band 1 = opaque cloud
# Band 2 = cirrus
# Band 3 = snow/ice
#
# Any detected cloud/cirrus/snow/ice pixel is masked.
# ============================================================

mask = (
    (opaque_cloud == 1)
    | (cirrus == 1)
    | (snow_ice == 1)
)


# ============================================================
# PROCESS NDWI
# ============================================================

with rasterio.open(NDWI_FILE) as src:

    ndwi = src.read(1)

    profile = src.profile.copy()

    total_pixels = ndwi.size

    if ndwi.shape != mask.shape:
        raise RuntimeError(
            f"NDWI and mask dimensions do not match: "
            f"{ndwi.shape} vs {mask.shape}"
        )

    ndwi_masked = ndwi.copy()

    ndwi_masked[mask] = np.nan


# ============================================================
# PROCESS MNDWI
# ============================================================

with rasterio.open(MNDWI_FILE) as src:

    mndwi = src.read(1)

    mndwi_profile = src.profile.copy()

    if mndwi.shape != mask.shape:
        raise RuntimeError(
            f"MNDWI and mask dimensions do not match: "
            f"{mndwi.shape} vs {mask.shape}"
        )

    mndwi_masked = mndwi.copy()

    mndwi_masked[mask] = np.nan


# ============================================================
# OUTPUT PROFILE
# ============================================================

profile.update(
    driver="GTiff",
    dtype="float32",
    count=1,
    compress="deflate",
    predictor=2,
    nodata=np.nan
)

mndwi_profile.update(
    driver="GTiff",
    dtype="float32",
    count=1,
    compress="deflate",
    predictor=2,
    nodata=np.nan
)


# ============================================================
# OUTPUT FILES
# ============================================================

ndwi_output = (
    OUTPUT /
    "S2B_20251230_NDWI_TOA_MASKED.tif"
)

mndwi_output = (
    OUTPUT /
    "S2B_20251230_MNDWI_TOA_MASKED.tif"
)


# ============================================================
# WRITE NDWI
# ============================================================

with rasterio.open(
    ndwi_output,
    "w",
    **profile
) as dst:

    dst.write(
        ndwi_masked.astype("float32"),
        1
    )


# ============================================================
# WRITE MNDWI
# ============================================================

with rasterio.open(
    mndwi_output,
    "w",
    **mndwi_profile
) as dst:

    dst.write(
        mndwi_masked.astype("float32"),
        1
    )


# ============================================================
# SUMMARY
# ============================================================

masked_pixels = int(np.count_nonzero(mask))
clear_pixels = total_pixels - masked_pixels

masked_percentage = (
    masked_pixels / total_pixels * 100
)

print("\n========================================")
print("MASKING COMPLETE")
print("========================================")

print(f"Grid: {mndwi.shape[1]} x {mndwi.shape[0]}")
print(f"Total pixels: {total_pixels:,}")
print(f"Masked pixels: {masked_pixels:,}")
print(f"Clear pixels: {clear_pixels:,}")
print(f"Masked percentage: {masked_percentage:.4f}%")

print("\nOutputs:")
print(ndwi_output)
print(mndwi_output)
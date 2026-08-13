from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling


# =========================================================
# PATHS
# =========================================================

BASE = Path("data/processed/sentinel2/2016_11_02")

SAFE = next(BASE.glob("*.SAFE"))
GRANULE = next(SAFE.glob("GRANULE/*"))

QI = GRANULE / "QI_DATA"

INDEX_DIR = Path("data/processed/sentinel2/indices")

NDWI_FILE = INDEX_DIR / "S2A_20161102_NDWI_TOA.tif"
MNDWI_FILE = INDEX_DIR / "S2A_20161102_MNDWI_TOA.tif"

MASK_FILE = QI / "MSK_CLASSI_B00.jp2"

OUTPUT_DIR = INDEX_DIR / "masked"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# READ NDWI GRID
# =========================================================

with rasterio.open(NDWI_FILE) as src:

    ndwi = src.read(1).astype("float32")

    profile = src.profile.copy()

    width = src.width
    height = src.height
    transform = src.transform
    crs = src.crs


# =========================================================
# READ MNDWI
# =========================================================

with rasterio.open(MNDWI_FILE) as src:

    mndwi = src.read(1).astype("float32")

    if src.width != width or src.height != height:
        raise RuntimeError("NDWI and MNDWI grids do not match.")

    if src.transform != transform:
        raise RuntimeError("NDWI and MNDWI transforms do not match.")

    if src.crs != crs:
        raise RuntimeError("NDWI and MNDWI CRS do not match.")


# =========================================================
# READ MSK_CLASSI
#
# Band 1 = opaque cloud
# Band 2 = cirrus
# Band 3 = snow/ice
#
# Source resolution = 60 m
# Target resolution = 10 m
#
# Nearest-neighbour is used because these are categorical
# mask values.
# =========================================================

with rasterio.open(MASK_FILE) as src:

    if src.count != 3:
        raise RuntimeError(
            f"Expected 3 MSK_CLASSI bands, found {src.count}"
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


# =========================================================
# CREATE VALID PIXEL MASK
#
# 0 = clear
# 1 = flagged
# =========================================================

cloud_mask = (
    (opaque_cloud == 1)
    | (cirrus == 1)
    | (snow_ice == 1)
)


# =========================================================
# APPLY MASK
# =========================================================

ndwi_masked = ndwi.copy()
mndwi_masked = mndwi.copy()

ndwi_masked[cloud_mask] = np.nan
mndwi_masked[cloud_mask] = np.nan


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
# WRITE MASKED NDWI
# =========================================================

ndwi_out = OUTPUT_DIR / "S2A_20161102_NDWI_TOA_MASKED.tif"

with rasterio.open(ndwi_out, "w", **profile) as dst:
    dst.write(ndwi_masked, 1)


# =========================================================
# WRITE MASKED MNDWI
# =========================================================

mndwi_out = OUTPUT_DIR / "S2A_20161102_MNDWI_TOA_MASKED.tif"

with rasterio.open(mndwi_out, "w", **profile) as dst:
    dst.write(mndwi_masked, 1)


# =========================================================
# VALIDATION
# =========================================================

total_pixels = height * width
masked_pixels = int(np.count_nonzero(cloud_mask))

valid_pixels = total_pixels - masked_pixels

print("\n========================================")
print("MASKING COMPLETE")
print("========================================")

print(f"Grid: {width} x {height}")
print(f"Total pixels: {total_pixels:,}")
print(f"Masked pixels: {masked_pixels:,}")
print(f"Clear pixels: {valid_pixels:,}")

print(
    f"Masked percentage: "
    f"{masked_pixels / total_pixels * 100:.4f}%"
)

print("\nOutputs:")
print(ndwi_out)
print(mndwi_out)
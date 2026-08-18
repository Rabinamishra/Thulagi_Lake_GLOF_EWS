from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.transform import xy
from scipy import ndimage


# =========================================================
# PATHS
# =========================================================

INPUT = Path(
    "data/processed/sentinel2/indices/masked/"
    "S2B_20251230_MNDWI_TOA_MASKED.tif"
)

OUTPUT_DIR = Path("data/processed/sentinel2/water")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "S2B_20251230_MNDWI_WATER_CANDIDATE.tif"

THRESHOLD = 0.30


# =========================================================
# READ MNDWI
# =========================================================

with rasterio.open(INPUT) as src:

    mndwi = src.read(1).astype("float32")
    profile = src.profile.copy()
    transform = src.transform
    crs = src.crs

    pixel_width = abs(transform.a)
    pixel_height = abs(transform.e)

    pixel_area_m2 = pixel_width * pixel_height


# =========================================================
# VALID PIXELS
# =========================================================

valid = np.isfinite(mndwi)


# =========================================================
# INITIAL WATER MASK
# =========================================================

water = valid & (mndwi >= THRESHOLD)


# =========================================================
# CONNECTED COMPONENT ANALYSIS
#
# 8-connected neighbourhood
# =========================================================

structure = np.ones((3, 3), dtype=np.uint8)

labels, number_of_features = ndimage.label(
    water,
    structure=structure
)


# =========================================================
# COMPONENT SIZES
# =========================================================

component_sizes = np.bincount(labels.ravel())

# Ignore background label 0
component_sizes[0] = 0

largest_labels = np.argsort(component_sizes)[::-1]


# =========================================================
# REPORT LARGEST COMPONENTS
# =========================================================

print("\n========================================")
print("CANDIDATE WATER EXTRACTION")
print("========================================")

print(f"MNDWI threshold: {THRESHOLD}")
print(f"Pixel size: {pixel_width:.2f} x {pixel_height:.2f} m")
print(f"Pixel area: {pixel_area_m2:.2f} m²")
print(f"Connected components: {number_of_features:,}")

print("\nLargest connected components:")

reported = 0

for label_id in largest_labels:

    if label_id == 0:
        continue

    size = component_sizes[label_id]

    if size == 0:
        continue

    area_km2 = size * pixel_area_m2 / 1_000_000

    print(
        f"Component {label_id}: "
        f"{size:,} pixels = {area_km2:.4f} km²"
    )

    reported += 1

    if reported >= 20:
        break


# =========================================================
# WRITE CANDIDATE WATER MASK
# =========================================================

profile.update(
    driver="GTiff",
    dtype="uint8",
    count=1,
    nodata=0,
    compress="deflate"
)

water_uint8 = water.astype("uint8")

with rasterio.open(OUTPUT, "w", **profile) as dst:
    dst.write(water_uint8, 1)


# =========================================================
# TOTAL CANDIDATE WATER AREA
# =========================================================

candidate_pixels = int(np.count_nonzero(water))

candidate_area_km2 = (
    candidate_pixels * pixel_area_m2 / 1_000_000
)

print("\nCandidate water pixels:")
print(f"{candidate_pixels:,}")

print(
    f"Candidate water area: "
    f"{candidate_area_km2:.4f} km²"
)

print("\nOutput:")
print(OUTPUT)
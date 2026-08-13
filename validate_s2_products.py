from pathlib import Path

import numpy as np
import rasterio


# =========================================================
# CONFIGURATION
# =========================================================

MASKED_DIR = Path(
    "data/processed/sentinel2/indices/masked"
)

DATES = [
    "20161102",
    "20181122",
    "20201231",
    "20221231",
    "20241220",
    "20251230",
]


# =========================================================
# VALIDATE ONE FILE
# =========================================================

def validate_file(path):

    with rasterio.open(path) as src:

        data = src.read(1)

        finite = np.isfinite(data)

        valid = data[finite]

        print(f"\nFile: {path.name}")
        print(f"  Dimensions : {src.width} x {src.height}")
        print(f"  CRS        : {src.crs}")
        print(f"  Resolution : {src.res}")
        print(f"  NoData     : {src.nodata}")
        print(f"  Valid      : {valid.size:,}")

        if valid.size > 0:
            print(f"  Minimum    : {np.min(valid):.4f}")
            print(f"  Maximum    : {np.max(valid):.4f}")
            print(f"  Mean       : {np.mean(valid):.4f}")
        else:
            print("  WARNING: NO VALID PIXELS")


# =========================================================
# MAIN
# =========================================================

print("=" * 65)
print("SENTINEL-2 MASKED PRODUCT VALIDATION")
print("=" * 65)

files_found = 0

for date in DATES:

    ndwi = (
        MASKED_DIR
        / f"S2A_{date}_NDWI_TOA_MASKED.tif"
    )

    mndwi = (
        MASKED_DIR
        / f"S2A_{date}_MNDWI_TOA_MASKED.tif"
    )

    print("\n" + "-" * 65)
    print(f"DATE: {date}")
    print("-" * 65)

    if ndwi.exists():
        validate_file(ndwi)
        files_found += 1
    else:
        print(f"  MISSING: {ndwi}")

    if mndwi.exists():
        validate_file(mndwi)
        files_found += 1
    else:
        print(f"  MISSING: {mndwi}")


print("\n" + "=" * 65)
print(f"FILES VALIDATED: {files_found}")
print("=" * 65)
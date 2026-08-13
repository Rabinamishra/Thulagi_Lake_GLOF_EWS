from pathlib import Path

import numpy as np
import rasterio


# =========================================================
# CONFIGURATION
# =========================================================

INDEX_DIR = Path("data/processed/sentinel2/indices/masked")

OUTPUT_DIR = Path("data/processed/sentinel2/indices/thresholds")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [0.00, 0.10, 0.20, 0.30, 0.40]


# =========================================================
# FIND MASKED MNDWI FILES
# =========================================================

files = sorted(INDEX_DIR.glob("*_MNDWI_TOA_MASKED.tif"))

if not files:
    raise FileNotFoundError(
        f"No masked MNDWI files found in:\n{INDEX_DIR}"
    )


print("=" * 62)
print("MNDWI THRESHOLD TESTING")
print("=" * 62)

print("\nInput directory:")
print(INDEX_DIR)

print("\nThresholds:")
print(THRESHOLDS)

print("\nFiles found:")
for f in files:
    print(" ", f.name)


# =========================================================
# PROCESS EACH YEAR
# =========================================================

for mndwi_file in files:

    # -----------------------------------------------------
    # Extract date from filename
    # -----------------------------------------------------

    name = mndwi_file.name

    date = name.replace(
        "_MNDWI_TOA_MASKED.tif", ""
    )

    print("\n" + "=" * 62)
    print(f"PROCESSING: {date}")
    print("=" * 62)

    # -----------------------------------------------------
    # Open MNDWI
    # -----------------------------------------------------

    with rasterio.open(mndwi_file) as src:

        profile = src.profile.copy()

        mndwi = src.read(1).astype("float32")

        height = src.height
        width = src.width

        transform = src.transform
        crs = src.crs

    # -----------------------------------------------------
    # Valid pixels
    # -----------------------------------------------------

    valid = np.isfinite(mndwi)

    valid_count = int(np.count_nonzero(valid))

    print(f"Grid: {width} x {height}")
    print(f"Valid pixels: {valid_count:,}")

    # -----------------------------------------------------
    # Create threshold masks
    # -----------------------------------------------------

    for threshold in THRESHOLDS:

        water_mask = np.zeros(
            mndwi.shape,
            dtype="uint8"
        )

        water_mask[
            valid & (mndwi > threshold)
        ] = 1

        water_pixels = int(
            np.count_nonzero(water_mask)
        )

        percentage = (
            water_pixels / valid_count * 100
            if valid_count > 0
            else 0
        )

        threshold_text = f"{threshold:.2f}".replace(
            ".", "_"
        )

        output_file = (
            OUTPUT_DIR
            / f"{date}_MNDWI_GT_{threshold_text}.tif"
        )

        output_profile = profile.copy()

        output_profile.update(
            driver="GTiff",
            dtype="uint8",
            count=1,
            nodata=0,
            compress="deflate"
        )

        with rasterio.open(
            output_file,
            "w",
            **output_profile
        ) as dst:

            dst.write(water_mask, 1)

        print(
            f"  > {threshold:.2f} : "
            f"{water_pixels:,} pixels "
            f"({percentage:.3f}%)"
        )

    # -----------------------------------------------------
    # Free memory
    # -----------------------------------------------------

    del mndwi


# =========================================================
# COMPLETE
# =========================================================

print("\n" + "=" * 62)
print("MNDWI THRESHOLD TESTING COMPLETE")
print("=" * 62)

print("\nOutputs:")
print(OUTPUT_DIR)
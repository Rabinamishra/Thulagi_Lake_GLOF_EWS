from pathlib import Path

import numpy as np
import rasterio


# =========================================================
# CONFIGURATION
# =========================================================

MASKED_DIR = Path(
    "data/processed/sentinel2/indices/masked"
)

PRODUCTS = [
    ("2016", "S2A_20161102_MNDWI_TOA_MASKED.tif"),
    ("2018", "S2A_20181122_MNDWI_TOA_MASKED.tif"),
    ("2020", "S2A_20201231_MNDWI_TOA_MASKED.tif"),
    ("2022", "S2A_20221231_MNDWI_TOA_MASKED.tif"),
    ("2024", "S2A_20241220_MNDWI_TOA_MASKED.tif"),
    ("2025", "S2B_20251230_MNDWI_TOA_MASKED.tif"),
]


# =========================================================
# ANALYSIS
# =========================================================

print("=" * 70)
print("MNDWI DISTRIBUTION ANALYSIS")
print("=" * 70)

for year, filename in PRODUCTS:

    path = MASKED_DIR / filename

    print("\n" + "=" * 70)
    print(f"YEAR: {year}")
    print("=" * 70)

    if not path.exists():
        print(f"MISSING: {path}")
        continue

    with rasterio.open(path) as src:

        data = src.read(1).astype("float32")

        valid = data[np.isfinite(data)]

        if valid.size == 0:
            print("ERROR: No valid pixels.")
            continue

        print(f"Valid pixels: {valid.size:,}")

        print("\nBasic statistics:")
        print(f"Minimum : {np.min(valid):.4f}")
        print(f"Maximum : {np.max(valid):.4f}")
        print(f"Mean    : {np.mean(valid):.4f}")
        print(f"Median  : {np.median(valid):.4f}")

        print("\nPercentiles:")

        percentiles = [
            1,
            2,
            5,
            10,
            20,
            25,
            50,
            75,
            80,
            90,
            95,
            98,
            99,
        ]

        values = np.percentile(valid, percentiles)

        for p, value in zip(percentiles, values):
            print(f"{p:>2}% : {value:.4f}")

        print("\nPixels above candidate thresholds:")

        for threshold in [
            -0.20,
            -0.10,
            0.00,
            0.05,
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
            0.40,
            0.50,
        ]:

            count = np.count_nonzero(valid > threshold)

            percentage = (
                count / valid.size * 100
            )

            print(
                f"MNDWI > {threshold:>5.2f}: "
                f"{count:>12,} pixels "
                f"({percentage:>7.3f}%)"
            )


print("\n" + "=" * 70)
print("MNDWI ANALYSIS COMPLETE")
print("=" * 70)
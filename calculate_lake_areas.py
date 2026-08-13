from pathlib import Path
import numpy as np
import rasterio

INPUT_DIR = Path("data/processed/sentinel2/indices/masked")
THRESHOLD = 0.30

files = {
    2016: "S2A_20161102_MNDWI_TOA_MASKED.tif",
    2018: "S2A_20181122_MNDWI_TOA_MASKED.tif",
    2020: "S2A_20201231_MNDWI_TOA_MASKED.tif",
    2022: "S2A_20221231_MNDWI_TOA_MASKED.tif",
    2024: "S2A_20241220_MNDWI_TOA_MASKED.tif",
    2025: "S2B_20251230_MNDWI_TOA_MASKED.tif",
}

print("\n========================================")
print("THULAGI LAKE AREA CALCULATION")
print("========================================")
print(f"MNDWI threshold: {THRESHOLD}")
print()

results = []

for year, filename in files.items():

    path = INPUT_DIR / filename

    with rasterio.open(path) as src:
        mndwi = src.read(1).astype("float32")

        pixel_width = abs(src.transform.a)
        pixel_height = abs(src.transform.e)
        pixel_area_m2 = pixel_width * pixel_height

        valid = np.isfinite(mndwi)
        water = valid & (mndwi >= THRESHOLD)

        water_pixels = int(np.count_nonzero(water))

        area_m2 = water_pixels * pixel_area_m2
        area_ha = area_m2 / 10_000
        area_km2 = area_m2 / 1_000_000

    results.append((year, water_pixels, area_m2, area_ha, area_km2))

    print(
        f"{year}: "
        f"{water_pixels:,} pixels | "
        f"{area_ha:.4f} ha | "
        f"{area_km2:.4f} km²"
    )

print("\n========================================")
print("SUMMARY")
print("========================================")

for year, pixels, area_m2, area_ha, area_km2 in results:
    print(f"{year}: {area_km2:.4f} km²")

print("========================================")
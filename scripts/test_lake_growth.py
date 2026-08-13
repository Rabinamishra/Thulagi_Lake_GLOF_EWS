from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask


# ============================================================
# THULAGI LAKE GROWTH TEST
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sentinel2"
    / "indices"
    / "masked"
)

GDB = PROJECT_ROOT / "GLOF_EWS" / "GLOF_EWS.gdb"

POLYGON_LAYER = "Thulagi_Polygon_Project"

MNDWI_THRESHOLD = 0.30

FILES = {
    2016: "S2A_20161102_MNDWI_TOA_MASKED.tif",
    2018: "S2A_20181122_MNDWI_TOA_MASKED.tif",
    2020: "S2A_20201231_MNDWI_TOA_MASKED.tif",
    2022: "S2A_20221231_MNDWI_TOA_MASKED.tif",
    2024: "S2A_20241220_MNDWI_TOA_MASKED.tif",
    2025: "S2B_20251230_MNDWI_TOA_MASKED.tif",
}


# Literature-anchored reference only.
DOCUMENTED_ANNUAL_GROWTH_RATE_PCT = (
    (0.94 - 0.72) / 0.72 / 30 * 100
)


print()
print("=" * 65)
print("THULAGI LAKE GROWTH TEST")
print("=" * 65)
print(f"MNDWI threshold: {MNDWI_THRESHOLD}")
print(f"Polygon: {POLYGON_LAYER}")
print(
    f"Documented reference growth rate: "
    f"~{DOCUMENTED_ANNUAL_GROWTH_RATE_PCT:.2f}%/year"
)
print()


# ============================================================
# 1. LOAD PROJECTED THULAGI POLYGON
# ============================================================

polygon = gpd.read_file(
    GDB,
    layer=POLYGON_LAYER
)
if polygon.empty:
    raise RuntimeError("Thulagi polygon layer is empty.")

print("Polygon CRS:")
print(polygon.crs)

print()


# ============================================================
# 2. CALCULATE LAKE AREA FOR EACH SENTINEL IMAGE
# ============================================================

results = []

for year, filename in FILES.items():

    raster_path = INPUT_DIR / filename

    if not raster_path.exists():
        raise FileNotFoundError(
            f"Raster not found:\n{raster_path}"
        )

    with rasterio.open(raster_path) as src:

        mndwi = src.read(1).astype("float32")

        # ----------------------------------------------------
        # Reproject polygon if necessary
        # ----------------------------------------------------

        polygon_for_raster = polygon.to_crs(src.crs)

        geometries = polygon_for_raster.geometry

        # ----------------------------------------------------
        # Create mask INSIDE the Thulagi polygon
        # ----------------------------------------------------

        inside_polygon = geometry_mask(
            geometries,
            transform=src.transform,
            invert=True,
            out_shape=(src.height, src.width),
        )

        # ----------------------------------------------------
        # Identify valid water pixels
        # ----------------------------------------------------

        valid = np.isfinite(mndwi)

        water = (
            valid
            & inside_polygon
            & (mndwi >= MNDWI_THRESHOLD)
        )

        water_pixels = int(np.count_nonzero(water))

        # Pixel dimensions
        pixel_width = abs(src.transform.a)
        pixel_height = abs(src.transform.e)

        pixel_area_m2 = pixel_width * pixel_height

        area_m2 = water_pixels * pixel_area_m2
        area_km2 = area_m2 / 1_000_000

    results.append(
        {
            "year": year,
            "water_pixels": water_pixels,
            "area_m2": area_m2,
            "area_km2": area_km2,
        }
    )

    print(
        f"{year}: "
        f"{water_pixels:,} water pixels | "
        f"{area_km2:.4f} km²"
    )


# ============================================================
# 3. YEAR-TO-YEAR CHANGE
# ============================================================

print()
print("=" * 65)
print("YEAR-TO-YEAR CHANGE")
print("=" * 65)

for previous, current in zip(results[:-1], results[1:]):

    years = current["year"] - previous["year"]

    change = current["area_km2"] - previous["area_km2"]

    pct_change = (
        change / previous["area_km2"] * 100
    )

    annualized = pct_change / years

    print(
        f"{previous['year']} -> {current['year']}: "
        f"{change:+.4f} km² | "
        f"{pct_change:+.2f}% total | "
        f"{annualized:+.2f}%/year"
    )


# ============================================================
# 4. OVERALL CHANGE
# ============================================================

first = results[0]
last = results[-1]

years_total = last["year"] - first["year"]

overall_change = (
    last["area_km2"] - first["area_km2"]
)

overall_pct = (
    overall_change / first["area_km2"] * 100
)

annualized_overall = overall_pct / years_total


print()
print("=" * 65)
print("OVERALL 2016-2025 CHANGE")
print("=" * 65)

print(
    f"2016 area:              "
    f"{first['area_km2']:.4f} km²"
)

print(
    f"2025 area:              "
    f"{last['area_km2']:.4f} km²"
)

print(
    f"Total change:           "
    f"{overall_change:+.4f} km²"
)

print(
    f"Total percentage:       "
    f"{overall_pct:+.2f}%"
)

print(
    f"Annualized change:      "
    f"{annualized_overall:+.2f}%/year"
)


# ============================================================
# 5. LITERATURE COMPARISON
# ============================================================

print()
print("=" * 65)
print("COMPARISON WITH DOCUMENTED LONG-TERM RATE")
print("=" * 65)

print(
    f"Our 2016-2025 annualized rate: "
    f"{annualized_overall:+.2f}%/year"
)

print(
    f"Literature-anchored reference: "
    f"~{DOCUMENTED_ANNUAL_GROWTH_RATE_PCT:.2f}%/year"
)

ratio = (
    annualized_overall
    / DOCUMENTED_ANNUAL_GROWTH_RATE_PCT
)

print(
    f"Rate ratio: "
    f"{ratio:.2f}x"
)

print()
print(
    "NOTE:"
)
print(
    "This comparison uses lake area extracted inside the "
    "Thulagi polygon. The literature rate is a long-term "
    "reference, not an operational GLOF threshold."
)
print(
    "Differences between individual satellite observations "
    "may reflect acquisition date, seasonal conditions, "
    "cloud/shadow masking, and shoreline extraction uncertainty."
)

print("=" * 65)
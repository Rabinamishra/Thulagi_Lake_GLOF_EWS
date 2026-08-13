import os
import geopandas as gpd
import rasterio
from rasterio.features import shapes
import numpy as np
from shapely.geometry import shape

DRAINAGE = r"C:\Users\mishr\Desktop\GLOF EWS\data\dem\thulagi_drainage_100cells.tif"
PATH = r"C:\Users\mishr\Desktop\GLOF EWS\data\spatial\thulagi_downstream_path_v2.geojson"
OUTPUT = r"C:\Users\mishr\Desktop\GLOF EWS\data\spatial\thulagi_potential_impact_corridor_v2.geojson"

print("=" * 60)
print("THULAGI POTENTIAL DOWNSTREAM IMPACT CORRIDOR")
print("=" * 60)

# ------------------------------------------------------------
# Load downstream path
# ------------------------------------------------------------

path = gpd.read_file(PATH)

# ------------------------------------------------------------
# Load drainage raster
# ------------------------------------------------------------

with rasterio.open(DRAINAGE) as src:

    drainage = src.read(1)
    transform = src.transform
    crs = src.crs
    nodata = src.nodata

    # Drainage cells
    mask = drainage > 0

    print("Drainage raster:", src.width, "x", src.height)
    print("CRS:", crs)
    print("Drainage cells:", int(np.sum(mask)))

    # Convert drainage cells to polygons
    polygons = []

    for geom, value in shapes(
        drainage,
        mask=mask,
        transform=transform
    ):
        if value > 0:
            polygons.append(shape(geom))

# ------------------------------------------------------------
# Create drainage corridor
# ------------------------------------------------------------

corridor = gpd.GeoDataFrame(
    {"feature": ["DEM-derived downstream drainage corridor"]},
    geometry=[gpd.GeoSeries(polygons, crs=crs).union_all()],
    crs=crs
)

# ------------------------------------------------------------
# Keep only drainage connected to the downstream path
# ------------------------------------------------------------

path_geom = path.geometry.iloc[0]

# Select drainage polygons intersecting the downstream path
connected = []

for geom in polygons:
    if geom.intersects(path_geom):
        connected.append(geom)

if not connected:
    raise RuntimeError(
        "No drainage cells intersect the downstream path."
    )

connected_geom = gpd.GeoSeries(
    connected,
    crs=crs
).union_all()

corridor = gpd.GeoDataFrame(
    {
        "feature": [
            "Thulagi DEM-derived potential downstream corridor"
        ],
        "source": [
            "D8 flow direction + drainage network"
        ],
        "path_length_m": [
            float(path_geom.length)
        ],
        "drainage_cells": [
            len(connected)
        ],
    },
    geometry=[connected_geom],
    crs=crs
)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True
)

corridor.to_file(
    OUTPUT,
    driver="GeoJSON"
)

print()
print("RESULT")
print("-" * 60)
print("Connected drainage features:", len(connected))
print(
    "Corridor area:",
    round(float(connected_geom.area) / 1e6, 4),
    "km²"
)
print(
    "Downstream path:",
    round(float(path_geom.length) / 1000, 3),
    "km"
)
print("Output:", OUTPUT)
print()
print("SUCCESS")
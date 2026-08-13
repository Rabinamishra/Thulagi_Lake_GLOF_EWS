import os
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import LineString


# ============================================================
# THULAGI LAKE — CORRECTED D8 DOWNSTREAM PATH
# ============================================================

FLOW_RASTER = r"data\dem\thulagi_flow_direction_extended.tif"
OUTPUT = r"data\spatial\thulagi_downstream_path_v2.geojson"

# ------------------------------------------------------------
# VERIFIED OUTLET / POUR POINT
# EPSG:32645 — WGS 84 / UTM Zone 45N
# ------------------------------------------------------------

OUTLET_X = 252988.8954270625
OUTLET_Y = 3155339.066442082

# Maximum number of cells to trace
MAX_STEPS = 2000

# ------------------------------------------------------------
# WhiteboxTools D8 pointer convention
#
# value : (row change, column change)
# ------------------------------------------------------------

D8 = {
    1:   (-1,  1),   # NE
    2:   ( 0,  1),   # E
    4:   ( 1,  1),   # SE
    8:   ( 1,  0),   # S
    16:  ( 1, -1),   # SW
    32:  ( 0, -1),   # W
    64:  (-1, -1),   # NW
    128: (-1,  0),   # N
}


print("=" * 60)
print("THULAGI CORRECTED D8 DOWNSTREAM PATH")
print("=" * 60)

# ------------------------------------------------------------
# Load flow-direction raster
# ------------------------------------------------------------

with rasterio.open(FLOW_RASTER) as src:

    flow = src.read(1)
    transform = src.transform
    crs = src.crs
    nodata = src.nodata
    height = src.height
    width = src.width

    # --------------------------------------------------------
    # Convert verified outlet coordinate to raster cell
    # --------------------------------------------------------

    row, col = src.index(OUTLET_X, OUTLET_Y)

    print(f"Raster size: {width} x {height}")
    print(f"CRS: {crs}")
    print(f"Outlet X: {OUTLET_X}")
    print(f"Outlet Y: {OUTLET_Y}")
    print(f"Outlet cell: row={row}, col={col}")

    # --------------------------------------------------------
    # Check outlet cell
    # --------------------------------------------------------

    outlet_value = flow[row, col]

    print(f"Outlet-cell D8 value: {outlet_value}")

    if outlet_value == nodata:
        raise RuntimeError(
            f"Outlet cell is NODATA: {outlet_value}"
        )

    if int(outlet_value) not in D8:
        raise RuntimeError(
            f"Outlet cell has invalid D8 value: {outlet_value}"
        )

    # --------------------------------------------------------
    # Print outlet elevation if available from DEM
    # --------------------------------------------------------

    print("Outlet D8 direction:", D8[int(outlet_value)])

    # --------------------------------------------------------
    # Trace downstream
    # --------------------------------------------------------

    path_cells = []
    visited = set()

    current_row = row
    current_col = col

    reason = "Maximum step limit reached"

    for step in range(MAX_STEPS):

        cell = (current_row, current_col)

        # Detect loops
        if cell in visited:
            reason = "Flow path entered a loop"
            break

        visited.add(cell)
        path_cells.append(cell)

        value = flow[current_row, current_col]

        # Stop at NODATA
        if value == nodata:
            reason = "Path reached NODATA cell"
            break

        # Stop if not a valid D8 direction
        if int(value) not in D8:
            reason = f"Path reached non-D8 cell (value={value})"
            break

        drow, dcol = D8[int(value)]

        next_row = current_row + drow
        next_col = current_col + dcol

        # Check raster boundary
        if (
            next_row < 0
            or next_row >= height
            or next_col < 0
            or next_col >= width
        ):
            reason = "Path reached raster boundary"
            break

        current_row = next_row
        current_col = next_col

    # --------------------------------------------------------
    # Convert raster cells to map coordinates
    # --------------------------------------------------------

    coordinates = []

    for r, c in path_cells:

        x, y = rasterio.transform.xy(
            transform,
            r,
            c,
            offset="center"
        )

        coordinates.append((x, y))

    if len(coordinates) < 2:
        raise RuntimeError(
            "Downstream path contains fewer than 2 cells."
        )

    line = LineString(coordinates)

    # --------------------------------------------------------
    # Calculate endpoint coordinates
    # --------------------------------------------------------

    endpoint_row = path_cells[-1][0]
    endpoint_col = path_cells[-1][1]

    endpoint_x, endpoint_y = rasterio.transform.xy(
        transform,
        endpoint_row,
        endpoint_col,
        offset="center"
    )

    # --------------------------------------------------------
    # Save output
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT),
        exist_ok=True
    )

    gdf = gpd.GeoDataFrame(
        {
            "feature": ["Thulagi corrected downstream D8 path"],
            "cells": [len(path_cells)],
            "start_row": [row],
            "start_col": [col],
            "end_row": [endpoint_row],
            "end_col": [endpoint_col],
            "stop_reason": [reason],
            "start_x": [OUTLET_X],
            "start_y": [OUTLET_Y],
            "end_x": [endpoint_x],
            "end_y": [endpoint_y],
        },
        geometry=[line],
        crs=crs,
    )

    gdf.to_file(
        OUTPUT,
        driver="GeoJSON"
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    distance_m = line.length

    print()
    print("RESULT")
    print("-" * 60)
    print(f"Downstream cells: {len(path_cells)}")
    print(f"Approx. path length: {distance_m:.1f} m")
    print(f"Endpoint row: {endpoint_row}")
    print(f"Endpoint col: {endpoint_col}")
    print(f"Endpoint X: {endpoint_x:.3f}")
    print(f"Endpoint Y: {endpoint_y:.3f}")
    print(f"Stop reason: {reason}")
    print(f"Output: {OUTPUT}")
    print()
    print("SUCCESS")
"""
THULAGI LAKE CONTEXT MAP
========================

Final spatial context map for the Thulagi Lake GLOF EWS prototype.

Shows:
    - Thulagi Lake (2025 Sentinel-2)
    - downstream flow path
    - potential impact corridor
    - north arrow
    - scale bar
    - coordinate grid
    - legend

INPUTS
------

Water raster:
data/processed/sentinel2/water/
S2B_20251230_MNDWI_WATER_CANDIDATE.tif

Downstream path:
data/spatial/thulagi_downstream_path_v2.geojson

Potential impact corridor:
data/spatial/thulagi_potential_impact_corridor_v2.geojson

OUTPUT
------

assets/thulagi_context_map.png
"""

# ============================================================
# IMPORTS
# ============================================================

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

import rasterio
from rasterio.features import shapes

import geopandas as gpd

from shapely.geometry import shape
from shapely.ops import unary_union


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"

ASSETS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# ============================================================
# INPUT FILES
# ============================================================

WATER_RASTER = (
    DATA_DIR
    / "processed"
    / "sentinel2"
    / "water"
    / "S2B_20251230_MNDWI_WATER_CANDIDATE.tif"
)

DOWNSTREAM_PATH = (
    DATA_DIR
    / "spatial"
    / "thulagi_downstream_path_v2.geojson"
)

IMPACT_CORRIDOR = (
    DATA_DIR
    / "spatial"
    / "thulagi_potential_impact_corridor_v2.geojson"
)

OUTPUT_MAP = (
    ASSETS_DIR
    / "thulagi_context_map.png"
)


# ============================================================
# VERIFIED 2025 LAKE RESULT
# ============================================================

EXPECTED_LAKE_PIXELS = 9291
EXPECTED_LAKE_AREA_KM2 = 0.9291


# ============================================================
# GEOMETRY CLEANING
# ============================================================

def clean_geometries(gdf, layer_name):
    """
    Clean invalid, empty and non-finite geometries.

    This is important because the potential impact corridor
    may contain invalid polygon geometries that can cause
    unary_union() or plotting extent calculations to return
    NaN/Inf.
    """

    if gdf.empty:
        print(f"{layer_name}: EMPTY")
        return gdf

    original_count = len(gdf)

    # Remove missing geometries
    gdf = gdf[
        gdf.geometry.notna()
    ].copy()

    # Remove empty geometries
    gdf = gdf[
        ~gdf.geometry.is_empty
    ].copy()

    # Attempt to repair invalid geometries
    repaired = []

    for geom in gdf.geometry:

        try:

            if not geom.is_valid:

                geom = geom.buffer(0)

            if geom is not None and not geom.is_empty:

                repaired.append(geom)

            else:

                repaired.append(None)

        except Exception:

            repaired.append(None)

    gdf = gdf.copy()

    gdf["geometry"] = repaired

    # Remove anything that could not be repaired
    gdf = gdf[
        gdf.geometry.notna()
    ].copy()

    gdf = gdf[
        ~gdf.geometry.is_empty
    ].copy()

    print(
        f"{layer_name}: "
        f"{original_count} → {len(gdf)} valid geometries"
    )

    return gdf


# ============================================================
# FIND LAKE COMPONENT
# ============================================================

def find_lake_component(
    water_data,
    transform,
):

    print()
    print(
        "Extracting connected water components..."
    )

    water_mask = (
        np.isfinite(water_data)
        & (water_data == 1)
    )

    total_water = int(
        water_mask.sum()
    )

    print(
        "Total water pixels in raster:",
        f"{total_water:,}",
    )

    components = []

    # --------------------------------------------------------
    # Polygonize connected components
    # --------------------------------------------------------

    for geom, value in shapes(
        water_mask.astype(np.uint8),
        mask=water_mask,
        transform=transform,
    ):

        if value != 1:
            continue

        polygon = shape(geom)

        if polygon.is_empty:
            continue

        try:

            if not polygon.is_valid:

                polygon = polygon.buffer(0)

        except Exception:

            continue

        if polygon.is_empty:
            continue

        pixel_area = abs(
            transform.a
            * transform.e
        )

        pixels = int(
            round(
                polygon.area
                / pixel_area
            )
        )

        components.append(
            (
                pixels,
                polygon,
            )
        )

    if not components:

        raise RuntimeError(
            "No connected water components were found."
        )

    components.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    print(
        "Connected components found:",
        f"{len(components):,}",
    )

    print()
    print(
        "Largest components:"
    )

    for i, (pixels, polygon) in enumerate(
        components[:15],
        start=1,
    ):

        area_km2 = (
            polygon.area
            / 1_000_000
        )

        print(
            f"  {i:02d}: "
            f"{pixels:,} pixels  "
            f"{area_km2:.4f} km²"
        )

    # --------------------------------------------------------
    # Select component closest to verified lake result
    # --------------------------------------------------------

    selected = min(
        components,
        key=lambda item:
        abs(
            item[0]
            - EXPECTED_LAKE_PIXELS
        ),
    )

    selected_pixels = selected[0]
    selected_polygon = selected[1]

    selected_area = (
        selected_polygon.area
        / 1_000_000
    )

    print()
    print(
        "SELECTED LAKE COMPONENT"
    )

    print(
        f"Pixels: {selected_pixels:,}"
    )

    print(
        f"Expected pixels: "
        f"{EXPECTED_LAKE_PIXELS:,}"
    )

    print(
        f"Difference: "
        f"{selected_pixels - EXPECTED_LAKE_PIXELS:+,}"
    )

    print(
        f"Area: {selected_area:.4f} km²"
    )

    print(
        f"Expected area: "
        f"{EXPECTED_LAKE_AREA_KM2:.4f} km²"
    )

    return selected_polygon


# ============================================================
# LOAD ALL SPATIAL DATA
# ============================================================

def load_layers():

    print()
    print("=" * 60)
    print("LOADING THULAGI SPATIAL DATA")
    print("=" * 60)

    # ========================================================
    # WATER RASTER
    # ========================================================

    if not WATER_RASTER.exists():

        raise FileNotFoundError(
            f"\nWater raster not found:\n{WATER_RASTER}"
        )

    with rasterio.open(
        WATER_RASTER
    ) as src:

        water = src.read(1)

        transform = src.transform

        raster_crs = src.crs

    print()
    print(
        "Water raster:",
        WATER_RASTER,
    )

    print(
        "CRS:",
        raster_crs,
    )

    print(
        "Resolution:",
        transform.a,
        abs(transform.e),
    )

    # ========================================================
    # LAKE
    # ========================================================

    lake_geometry = find_lake_component(
        water,
        transform,
    )

    lake = gpd.GeoDataFrame(
        {
            "name": [
                "Thulagi Lake"
            ]
        },
        geometry=[
            lake_geometry
        ],
        crs=raster_crs,
    )

    # ========================================================
    # DOWNSTREAM PATH
    # ========================================================

    if not DOWNSTREAM_PATH.exists():

        raise FileNotFoundError(
            f"\nDownstream path not found:\n"
            f"{DOWNSTREAM_PATH}"
        )

    downstream = gpd.read_file(
        DOWNSTREAM_PATH
    )

    print()
    print(
        "Downstream path:"
    )

    print(
        DOWNSTREAM_PATH
    )

    print(
        "Features:",
        len(downstream),
    )

    print(
        "CRS:",
        downstream.crs,
    )

    downstream = clean_geometries(
        downstream,
        "Downstream path",
    )

    # ========================================================
    # IMPACT CORRIDOR
    # ========================================================

    if not IMPACT_CORRIDOR.exists():

        raise FileNotFoundError(
            f"\nImpact corridor not found:\n"
            f"{IMPACT_CORRIDOR}"
        )

    corridor = gpd.read_file(
        IMPACT_CORRIDOR
    )

    print()
    print(
        "Potential impact corridor:"
    )

    print(
        IMPACT_CORRIDOR
    )

    print(
        "Features:",
        len(corridor),
    )

    print(
        "CRS:",
        corridor.crs,
    )

    corridor = clean_geometries(
        corridor,
        "Impact corridor",
    )

    # ========================================================
    # REPROJECT
    # ========================================================

    if downstream.crs is None:

        raise RuntimeError(
            "Downstream path has no CRS."
        )

    if corridor.crs is None:

        raise RuntimeError(
            "Impact corridor has no CRS."
        )

    if downstream.crs != raster_crs:

        downstream = downstream.to_crs(
            raster_crs
        )

    if corridor.crs != raster_crs:

        corridor = corridor.to_crs(
            raster_crs
        )

    print()
    print(
        "All spatial layers converted to:",
        raster_crs,
    )

    return (
        lake,
        downstream,
        corridor,
        raster_crs,
    )


# ============================================================
# GET SAFE BOUNDS
# ============================================================

def get_safe_bounds(
    lake,
    downstream,
    corridor,
):

    """
    Calculate map bounds while ignoring invalid or
    non-finite geometry bounds.
    """

    all_bounds = []

    for name, gdf in [
        ("Lake", lake),
        ("Downstream", downstream),
        ("Corridor", corridor),
    ]:

        if gdf.empty:
            continue

        try:

            bounds = gdf.total_bounds

            if len(bounds) != 4:
                continue

            if not np.all(
                np.isfinite(bounds)
            ):
                print(
                    f"WARNING: "
                    f"{name} bounds are invalid."
                )
                continue

            xmin, ymin, xmax, ymax = bounds

            if xmax <= xmin:
                print(
                    f"WARNING: "
                    f"{name} has invalid X bounds."
                )
                continue

            if ymax <= ymin:
                print(
                    f"WARNING: "
                    f"{name} has invalid Y bounds."
                )
                continue

            all_bounds.append(
                bounds
            )

        except Exception as exc:

            print(
                f"WARNING: Could not read "
                f"{name} bounds: {exc}"
            )

    if not all_bounds:

        raise RuntimeError(
            "No valid spatial bounds could be calculated."
        )

    all_bounds = np.asarray(
        all_bounds,
        dtype=float,
    )

    xmin = np.min(
        all_bounds[:, 0]
    )

    ymin = np.min(
        all_bounds[:, 1]
    )

    xmax = np.max(
        all_bounds[:, 2]
    )

    ymax = np.max(
        all_bounds[:, 3]
    )

    if not all(
        np.isfinite(
            [xmin, ymin, xmax, ymax]
        )
    ):

        raise RuntimeError(
            "Final map bounds contain NaN or Inf."
        )

    return (
        xmin,
        ymin,
        xmax,
        ymax,
    )


# ============================================================
# NORTH ARROW
# ============================================================

def add_north_arrow(ax):

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    x = (
        xmin
        + 0.92
        * (xmax - xmin)
    )

    y = (
        ymin
        + 0.78
        * (ymax - ymin)
    )

    length = (
        0.08
        * (ymax - ymin)
    )

    ax.annotate(
        "",
        xy=(
            x,
            y + length,
        ),
        xytext=(
            x,
            y,
        ),
        arrowprops=dict(
            arrowstyle="-|>",
            linewidth=2,
            color="black",
        ),
        zorder=100,
    )

    ax.text(
        x,
        y + length * 1.08,
        "N",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        zorder=101,
    )


# ============================================================
# SCALE BAR
# ============================================================

def add_scale_bar(
    ax,
    length_m=1000,
):

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    width = xmax - xmin
    height = ymax - ymin

    # If map is too small, shorten scale bar
    if width < 2500:

        length_m = 500

    x_start = (
        xmin
        + 0.07
        * width
    )

    y_start = (
        ymin
        + 0.06
        * height
    )

    ax.plot(
        [
            x_start,
            x_start + length_m,
        ],
        [
            y_start,
            y_start,
        ],
        color="black",
        linewidth=4,
        solid_capstyle="butt",
        zorder=100,
    )

    tick_height = (
        0.012
        * height
    )

    ax.plot(
        [
            x_start,
            x_start,
        ],
        [
            y_start - tick_height,
            y_start + tick_height,
        ],
        color="black",
        linewidth=2,
        zorder=100,
    )

    ax.plot(
        [
            x_start + length_m,
            x_start + length_m,
        ],
        [
            y_start - tick_height,
            y_start + tick_height,
        ],
        color="black",
        linewidth=2,
        zorder=100,
    )

    label = (
        f"{length_m / 1000:g} km"
    )

    ax.text(
        x_start + length_m / 2,
        y_start + 0.02 * height,
        label,
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold",
        zorder=101,
    )


# ============================================================
# DOWNSTREAM END LABEL
# ============================================================

def add_downstream_label(
    ax,
    downstream,
):

    if downstream.empty:
        return

    try:

        geom = unary_union(
            list(
                downstream.geometry
            )
        )

        if geom is None or geom.is_empty:
            return

        # ----------------------------------------------------
        # Handle LineString
        # ----------------------------------------------------

        if geom.geom_type == "LineString":

            endpoint = list(
                geom.coords
            )[-1]

        # ----------------------------------------------------
        # Handle MultiLineString
        # ----------------------------------------------------

        elif geom.geom_type == "MultiLineString":

            longest = max(
                geom.geoms,
                key=lambda line:
                line.length,
            )

            endpoint = list(
                longest.coords
            )[-1]

        else:

            return

        ax.text(
            endpoint[0],
            endpoint[1],
            "Downstream",
            fontsize=8,
            fontweight="bold",
            ha="left",
            va="bottom",
            zorder=30,
            bbox=dict(
                facecolor="white",
                edgecolor="none",
                alpha=0.7,
                pad=2,
            ),
        )

    except Exception as exc:

        print(
            "WARNING: Could not add "
            f"downstream label: {exc}"
        )


# ============================================================
# CREATE MAP
# ============================================================

def create_map():

    (
        lake,
        downstream,
        corridor,
        crs,
    ) = load_layers()

    # ========================================================
    # SAFE MAP EXTENT
    # ========================================================

    xmin, ymin, xmax, ymax = get_safe_bounds(
        lake,
        downstream,
        corridor,
    )

    width = xmax - xmin
    height = ymax - ymin

    # --------------------------------------------------------
    # Protect against extremely small extents
    # --------------------------------------------------------

    if width <= 0 or height <= 0:

        raise RuntimeError(
            "Invalid map extent."
        )

    padding_x = max(
        width * 0.08,
        100,
    )

    padding_y = max(
        height * 0.08,
        100,
    )

    map_xmin = xmin - padding_x
    map_xmax = xmax + padding_x

    map_ymin = ymin - padding_y
    map_ymax = ymax + padding_y

    # Final safety check
    if not np.all(
        np.isfinite(
            [
                map_xmin,
                map_xmax,
                map_ymin,
                map_ymax,
            ]
        )
    ):

        raise RuntimeError(
            "Map extent contains NaN or Inf."
        )

    # ========================================================
    # FIGURE
    # ========================================================

    fig, ax = plt.subplots(
        figsize=(11, 8.5),
        dpi=200,
    )

    ax.set_facecolor(
        "#eef2f7"
    )

    # ========================================================
    # IMPACT CORRIDOR
    # ========================================================

    if not corridor.empty:

        corridor.plot(
            ax=ax,
            facecolor="#f4a261",
            edgecolor="#d97706",
            linewidth=0.5,
            alpha=0.35,
            zorder=1,
        )

    # ========================================================
    # DOWNSTREAM PATH
    # ========================================================

    if not downstream.empty:

        downstream.plot(
            ax=ax,
            color="#7b2cbf",
            linewidth=2.5,
            zorder=5,
        )

    # ========================================================
    # LAKE
    # ========================================================

    lake.plot(
        ax=ax,
        facecolor="#4f81bd",
        edgecolor="black",
        linewidth=2,
        alpha=0.90,
        zorder=10,
    )

    # ========================================================
    # LAKE LABEL
    # ========================================================

    lake_centroid = (
        lake.geometry.iloc[0].centroid
    )

    ax.text(
        lake_centroid.x,
        lake_centroid.y,
        "THULAGI\nLAKE",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="black",
        zorder=20,
        bbox=dict(
            facecolor="white",
            edgecolor="none",
            alpha=0.65,
            pad=2,
        ),
    )

    # ========================================================
    # DOWNSTREAM LABEL
    # ========================================================

    add_downstream_label(
        ax,
        downstream,
    )

    # ========================================================
    # EXTENT
    # ========================================================

    ax.set_xlim(
        map_xmin,
        map_xmax,
    )

    ax.set_ylim(
        map_ymin,
        map_ymax,
    )

    # ========================================================
    # TITLE
    # ========================================================

    ax.set_title(
        "THULAGI LAKE — GLOF DECISION-SUPPORT CONTEXT",
        fontsize=15,
        fontweight="bold",
        pad=16,
    )

    ax.text(
        0.5,
        1.015,
        (
            "2025 Sentinel-2 lake extent • "
            "downstream flow path • "
            "potential impact corridor"
        ),
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
    )

    # ========================================================
    # AXES
    # ========================================================

    ax.set_xlabel(
        "Easting (m)",
        fontsize=9,
    )

    ax.set_ylabel(
        "Northing (m)",
        fontsize=9,
    )

    ax.tick_params(
        labelsize=8
    )

    ax.grid(
        True,
        linestyle="--",
        linewidth=0.5,
        alpha=0.25,
    )

    # ========================================================
    # NORTH ARROW
    # ========================================================

    add_north_arrow(
        ax
    )

    # ========================================================
    # SCALE BAR
    # ========================================================

    add_scale_bar(
        ax,
        length_m=1000,
    )

    # ========================================================
    # LEGEND
    # ========================================================

    legend_items = [

        Patch(
            facecolor="#4f81bd",
            edgecolor="black",
            label="Thulagi Lake (2025)",
        ),

        Patch(
            facecolor="#f4a261",
            edgecolor="#d97706",
            alpha=0.35,
            label="Potential impact corridor",
        ),

        Line2D(
            [0],
            [0],
            color="#7b2cbf",
            linewidth=2.5,
            label="Downstream flow path",
        ),
    ]

    ax.legend(
        handles=legend_items,
        loc="upper right",
        fontsize=8,
        frameon=True,
        framealpha=0.95,
        title="Map layers",
        title_fontsize=9,
    )

    # ========================================================
    # FOOTNOTE
    # ========================================================

    fig.text(
        0.5,
        0.015,
        (
            "Research prototype • Spatial context derived "
            "from Sentinel-2 and downstream hydrologic analysis"
        ),
        ha="center",
        fontsize=7.5,
    )

    # ========================================================
    # SAVE
    # ========================================================

    fig.tight_layout(
        rect=[
            0,
            0.035,
            1,
            1,
        ]
    )

    fig.savefig(
        OUTPUT_MAP,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    # ========================================================
    # SUCCESS
    # ========================================================

    print()
    print("=" * 60)
    print("MAP CREATED SUCCESSFULLY")
    print("=" * 60)

    print()
    print(
        "Output:"
    )

    print(
        OUTPUT_MAP
    )

    print()
    print(
        "Lake area:"
    )

    print(
        f"  Verified 2025 area: "
        f"{EXPECTED_LAKE_AREA_KM2:.4f} km²"
    )

    print()
    print(
        "Downstream path:"
    )

    print(
        "  thulagi_downstream_path_v2.geojson"
    )

    print()
    print(
        "Impact corridor:"
    )

    print(
        "  thulagi_potential_impact_corridor_v2.geojson"
    )

    print()
    print(
        "CRS:"
    )

    print(
        f"  {crs}"
    )

    print()
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    create_map()
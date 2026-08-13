import os
import geopandas as gpd


# ============================================================
# THULAGI GLOF EWS — OSM EXPOSURE EXTRACTION
# ============================================================

OSM_DIR = r"C:\Users\mishr\Desktop\geo\Nepal_Shp\osm"

CORRIDOR = r"data\spatial\thulagi_potential_impact_corridor.geojson"

OUTPUT_DIR = r"data\spatial\exposure"

BUILDINGS = os.path.join(
    OSM_DIR,
    "gis_osm_buildings_a_free_1.shp"
)

ROADS = os.path.join(
    OSM_DIR,
    "gis_osm_roads_free_1.shp"
)

PLACES = os.path.join(
    OSM_DIR,
    "gis_osm_places_free_1.shp"
)

POIS = os.path.join(
    OSM_DIR,
    "gis_osm_pois_free_1.shp"
)


print("=" * 60)
print("THULAGI GLOF EWS — OSM EXPOSURE EXTRACTION")
print("=" * 60)


# ------------------------------------------------------------
# Load corridor
# ------------------------------------------------------------

corridor = gpd.read_file(CORRIDOR)

print("Corridor CRS:", corridor.crs)
print("Corridor area:",
      round(corridor.geometry.area.iloc[0] / 1e6, 4),
      "km²")


# Convert corridor to WGS84 for efficient OSM bbox filtering
corridor_wgs84 = corridor.to_crs(4326)

bbox = tuple(corridor_wgs84.total_bounds)

print("OSM bounding box:")
print(bbox)


# ------------------------------------------------------------
# Prepare output directory
# ------------------------------------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ------------------------------------------------------------
# Function for extraction
# ------------------------------------------------------------

def extract_layer(path, name):

    print()
    print("-" * 60)
    print("PROCESSING:", name)
    print("-" * 60)

    if not os.path.exists(path):
        print("FILE NOT FOUND:", path)
        return None

    print("Reading only features inside corridor bounding box...")

    data = gpd.read_file(
        path,
        bbox=bbox
    )

    print("Features inside bounding box:", len(data))

    if len(data) == 0:
        print("No features found.")
        return None

    # Match corridor CRS
    data = data.to_crs(corridor.crs)

    # Actual intersection with corridor
    intersecting = data[
        data.geometry.intersects(
            corridor.geometry.iloc[0]
        )
    ].copy()

    print(
        "Features intersecting corridor:",
        len(intersecting)
    )

    return intersecting


# ------------------------------------------------------------
# BUILDINGS
# ------------------------------------------------------------

buildings = extract_layer(
    BUILDINGS,
    "BUILDINGS"
)

if buildings is not None and len(buildings) > 0:

    out = os.path.join(
        OUTPUT_DIR,
        "thulagi_buildings_exposed.geojson"
    )

    buildings.to_file(
        out,
        driver="GeoJSON"
    )

    print("Saved:", out)


# ------------------------------------------------------------
# ROADS
# ------------------------------------------------------------

roads = extract_layer(
    ROADS,
    "ROADS"
)

if roads is not None and len(roads) > 0:

    out = os.path.join(
        OUTPUT_DIR,
        "thulagi_roads_exposed.geojson"
    )

    roads.to_file(
        out,
        driver="GeoJSON"
    )

    print("Saved:", out)


# ------------------------------------------------------------
# PLACES
# ------------------------------------------------------------

places = extract_layer(
    PLACES,
    "PLACES"
)

if places is not None and len(places) > 0:

    out = os.path.join(
        OUTPUT_DIR,
        "thulagi_places_exposed.geojson"
    )

    places.to_file(
        out,
        driver="GeoJSON"
    )

    print("Saved:", out)


# ------------------------------------------------------------
# POIs
# ------------------------------------------------------------

pois = extract_layer(
    POIS,
    "POINTS OF INTEREST"
)

if pois is not None and len(pois) > 0:

    out = os.path.join(
        OUTPUT_DIR,
        "thulagi_pois_exposed.geojson"
    )

    pois.to_file(
        out,
        driver="GeoJSON"
    )

    print("Saved:", out)


print()
print("=" * 60)
print("EXPOSURE EXTRACTION COMPLETE")
print("=" * 60)
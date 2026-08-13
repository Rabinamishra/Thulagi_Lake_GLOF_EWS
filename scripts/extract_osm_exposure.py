import os
import geopandas as gpd

# ============================================================
# THULAGI GLOF EWS - OSM EXPOSURE EXTRACTION
# ============================================================

OSM_DIR = r"C:\Users\mishr\Desktop\geo\Nepal_Shp\osm"
CORRIDOR = r"C:\Users\mishr\Desktop\GLOF EWS\data\spatial\thulagi_potential_impact_corridor_v2.geojson"

OUTPUT_DIR = r"C:\Users\mishr\Desktop\GLOF EWS\data\spatial\exposure"

os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_CRS = "EPSG:32645"

layers = {
    "buildings": "gis_osm_buildings_a_free_1.shp",
    "roads": "gis_osm_roads_free_1.shp",
    "places": "gis_osm_places_free_1.shp",
    "pois": "gis_osm_pois_free_1.shp",
}

print("\nTHULAGI OSM EXPOSURE EXTRACTION")
print("=" * 55)

# ------------------------------------------------------------
# Read corrected impact corridor
# ------------------------------------------------------------

corridor = gpd.read_file(CORRIDOR)

if corridor.empty:
    raise RuntimeError("Impact corridor is empty.")

corridor = corridor.to_crs(TARGET_CRS)

corridor_area = corridor.geometry.area.sum()

print(f"Corridor CRS: {corridor.crs}")
print(f"Corridor features: {len(corridor)}")
print(f"Corridor area: {corridor_area:,.2f} m²")
print(f"Corridor area: {corridor_area / 1e6:.6f} km²")

# Dissolve to one geometry for intersection
corridor_geom = corridor.dissolve()

# Bounding box in OSM CRS
corridor_wgs84 = corridor_geom.to_crs("EPSG:4326")
bbox = tuple(corridor_wgs84.total_bounds)

print("\nSpatial filter:")
print(f"Bounding box: {bbox}")

# ------------------------------------------------------------
# Process each OSM layer
# ------------------------------------------------------------

results = {}

for name, filename in layers.items():

    path = os.path.join(OSM_DIR, filename)

    print("\n" + "-" * 55)
    print(f"Processing: {name}")
    print(f"Source: {filename}")

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # Read only features within the corridor bounding box
    gdf = gpd.read_file(path, bbox=bbox)

    print(f"Features in bounding box: {len(gdf)}")

    if gdf.empty:
        print("No features found.")
        results[name] = 0
        continue

    # Reproject to corridor CRS
    gdf = gdf.to_crs(TARGET_CRS)

    # Keep only features that actually intersect the corridor
    mask = gdf.geometry.intersects(corridor_geom.geometry.iloc[0])
    exposed = gdf.loc[mask].copy()

    print(f"Features intersecting corridor: {len(exposed)}")

    # Save exposed features
    output = os.path.join(
        OUTPUT_DIR,
        f"thulagi_{name}_exposed_FINAL.geojson"
    )

    exposed.to_file(output, driver="GeoJSON")

    print(f"Saved: {output}")

    results[name] = len(exposed)

# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

print("\n")
print("=" * 55)
print("FINAL EXPOSURE SUMMARY")
print("=" * 55)

print(f"Buildings          : {results.get('buildings', 0)}")
print(f"Road segments      : {results.get('roads', 0)}")
print(f"Settlements/places : {results.get('places', 0)}")
print(f"POIs               : {results.get('pois', 0)}")

print("\nOutput directory:")
print(OUTPUT_DIR)

print("\nEXTRACTION COMPLETE")
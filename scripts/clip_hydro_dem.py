import rasterio
import geopandas as gpd
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling

input_dem = r"C:\Users\mishr\Desktop\geo\Nepal_Shp\DEM\Nepal_DEM.tif"
aoi_file = r"data\dem\thulagi_hydro_aoi.geojson"

wgs84_file = r"data\dem\thulagi_hydro_wgs84.tif"
output_file = r"data\dem\thulagi_hydro_dem_utm45.tif"

aoi = gpd.read_file(aoi_file).to_crs(4326)

with rasterio.open(input_dem) as src:
    clipped, transform = mask(src, aoi.geometry, crop=True)

    profile = src.profile.copy()
    profile.update(
        height=clipped.shape[1],
        width=clipped.shape[2],
        transform=transform
    )

    with rasterio.open(wgs84_file, "w", **profile) as dst:
        dst.write(clipped)

with rasterio.open(wgs84_file) as src:

    transform2, width2, height2 = calculate_default_transform(
        src.crs,
        "EPSG:32645",
        src.width,
        src.height,
        *src.bounds
    )

    profile2 = src.profile.copy()
    profile2.update(
        crs="EPSG:32645",
        transform=transform2,
        width=width2,
        height=height2
    )

    with rasterio.open(output_file, "w", **profile2) as dst:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform2,
            dst_crs="EPSG:32645",
            resampling=Resampling.bilinear
        )

print("DONE:", output_file)
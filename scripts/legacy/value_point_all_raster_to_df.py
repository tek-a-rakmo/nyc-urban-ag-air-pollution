import os
import tempfile
import pandas as pd
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
)
import processing

# --- Function to process a single raster and return a DataFrame ---
def process_raster_sample_points(raster_path, point_layer, target_crs, column_prefix, last_folder_name):
    print(f"Processing raster: {raster_path}")

    raster_layer = QgsRasterLayer(raster_path, "PollutionRaster", "gdal")
    if not raster_layer.isValid():
        print(f"Raster path is NOT valid: {raster_path}")
        return None
    # Get the extent of the raster layer
    raster_extent = raster_layer.extent()
    print("Raster extent:", raster_extent)
    
    # Temporary output paths
    tmp_raster_file = os.path.join(tempfile.gettempdir(), f"reprojected_{os.path.basename(raster_path)}.tif")
    tmp_output_file = os.path.join(tempfile.gettempdir(), f"sample_{last_folder_name}.gpkg")
    reprojected_points_uri = os.path.join(tempfile.gettempdir(), f"reprojected_{os.path.basename(raster_path)}.gpkg")
    
    print("This is output vector", reprojected_points_uri)

    # --- Step 1: Reproject Raster ---
    reproject_raster_params = {
        'INPUT': raster_path,
        'RESAMPLING': 0,
        'TARGET_CRS': target_crs,
        'OUTPUT': tmp_raster_file
    }
    processing.run("gdal:warpreproject", reproject_raster_params)
    reprojected_raster_layer = QgsRasterLayer(tmp_raster_file, "ReprojectedRaster", "gdal")
    
    # Get the extent of the raster reprojected layer
    raster_extent = reprojected_raster_layer.extent()
    print("Raster reprojected extent:", reprojected_raster_layer)
    
    # --- Step 2: Reproject Points ---
    reproject_points_params = {
        'INPUT': point_layer,
        'CONVERT_CURVED_GEOMETRIES': False,
        'OPERATION': '',
        'TARGET_CRS': target_crs.toWkt(),
        'OUTPUT': reprojected_points_uri
    }
    processing.run("native:reprojectlayer", reproject_points_params)
    reprojected_point_layer = QgsVectorLayer(reprojected_points_uri, "ReprojectedPoints", "memory")

    
    # --- Debug: Check point count ---
    print(f"Point layer has {reprojected_point_layer.featureCount()} points")
    
    # --- Step 3: Sample Raster Values ---
    sample_params = {
        'COLUMN_PREFIX': last_folder_name + "_" + column_prefix,
        'INPUT': reprojected_point_layer,
        'RASTERCOPY': reprojected_raster_layer,
        'OUTPUT': tmp_output_file
    }
    processing.run('native:rastersampling', sample_params)

    # --- Step 4: Read output into DataFrame ---
    sampled_layer = QgsVectorLayer(tmp_output_file, "SampledPoints", "ogr")
    if not sampled_layer.isValid():
        print(f"Failed to read sampled layer from {tmp_output_file}")
        return None

    features = sampled_layer.getFeatures()
    field_names = [field.name() for field in sampled_layer.fields()]

    data = []
    for feat in features:
        attr = [feat[field] for field in field_names]
        geom = feat.geometry()
        if geom and not geom.isEmpty():
            point = geom.asPoint()
            attr.append(point.x())
            attr.append(point.y())
        else:
            attr.extend([None, None])
        data.append(attr)

    df = pd.DataFrame(data, columns=field_names + ["X", "Y"])
    df["source"] = last_folder_name  # Optional column to track source
    return df


# --- USER INPUTS ---
input_point_layer_path = r"D:\PLSCI 5200\Final_Project_GIS\Data\nyc_moua\nyc_moua.gpkg"
root_raster_folder = r"D:\PLSCI 5200\Final_Project_GIS\Data\air-quality\air_quality_NYCCAS\AnnAvg_1_15_300m\AnnAvg_1_15_300m"
target_crs_epsg = "EPSG:4236"
column_prefix = "sample"
# ---------------------

# Load the point layer
point_layer = QgsVectorLayer(input_point_layer_path, "UrbanAgSites", "ogr")
if not point_layer.isValid():
    print(f"Error: Could not load point layer: {input_point_layer_path}")
    exit()
# --- Debug: Check point count ---
print(f"Point layer has {point_layer.featureCount()} points")

target_crs = QgsCoordinateReferenceSystem(target_crs_epsg)

# --- Loop through folders and collect samples ---
all_samples = []

for dirpath, dirnames, filenames in os.walk(root_raster_folder):
    if "hdr.adf" in filenames:
        raster_file_path = dirpath  # Use the directory directly for .adf rasters
        last_folder_name = os.path.basename(dirpath)
        df = process_raster_sample_points(raster_file_path, point_layer, target_crs, column_prefix, last_folder_name)
        if df is not None:
            all_samples.append(df)

# Combine all DataFrames
final_df = pd.concat(all_samples, ignore_index=True)
print("✅ All samples collected. Final DataFrame shape:", final_df.shape)

# Optional: Save to CSV
final_df.to_csv(r"D:\PLSCI 5200\Final_Project_GIS\sampled_points_output.csv", index=False)

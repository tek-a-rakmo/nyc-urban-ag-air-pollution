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

    # --- Step 1: Reproject Raster ---
    tmp_raster_file = os.path.join(tempfile.gettempdir(), f"reprojected_{os.path.basename(raster_path)}.tif")
    reproject_raster_params = {
        'DATA_TYPE': 0,
        'EXTRA': '',
        'INPUT': raster_path,
        'MULTITHREADING': False,
        'NODATA': None,
        'OPTIONS': '',
        'RESAMPLING': 0,
        'SOURCE_CRS': None,
        'TARGET_CRS': target_crs.toWkt(),
        'TARGET_EXTENT': None,
        'TARGET_EXTENT_CRS': None,
        'TARGET_RESOLUTION': None,
        'OUTPUT': tmp_raster_file
    }
    processing.run('gdal:warpreproject', reproject_raster_params)

    # --- Step 2: Reproject Vector Layer ---
    tmp_reprojected_vector = os.path.join(tempfile.gettempdir(), f"reprojected_vector_{last_folder_name}.gpkg")
    reproject_points_params = {
        'INPUT': point_layer,
        'CONVERT_CURVED_GEOMETRIES': False,
        'OPERATION': '',
        'TARGET_CRS': target_crs.toWkt(),
        'OUTPUT': tmp_reprojected_vector
    }
    processing.run('native:reprojectlayer', reproject_points_params)
    reprojected_point_layer = QgsVectorLayer(tmp_reprojected_vector, "ReprojectedPoints", "ogr")

    if not reprojected_point_layer.isValid():
        print("❌ Reprojected point layer is invalid")
        return None

    print(f"✅ Reprojected point layer has {reprojected_point_layer.featureCount()} features")

    # --- Step 3: Raster Sampling ---
    tmp_sampled_output = os.path.join(tempfile.gettempdir(), f"sampled_{last_folder_name}.gpkg")
    sample_params = {
        'COLUMN_PREFIX': last_folder_name + "_" + column_prefix,
        'INPUT': reprojected_point_layer,
        'RASTERCOPY': tmp_raster_file,
        'OUTPUT': tmp_sampled_output
    }
    processing.run('native:rastersampling', sample_params)

    # --- Step 4: Read Output into DataFrame ---
    sampled_layer = QgsVectorLayer(tmp_sampled_output, "SampledPoints", "ogr")
    if not sampled_layer.isValid():
        print("❌ Sampled layer is invalid")
        return None

    features = sampled_layer.getFeatures()
    field_names = [field.name() for field in sampled_layer.fields()]

    # Find the sample column (the one that starts with the COLUMN_PREFIX)
    sample_columns = [field for field in field_names if field.startswith(last_folder_name + "_" + column_prefix)]
    if not sample_columns:
        print("❌ No sample column found in layer")
        return None
    sample_column = sample_columns[0]  # assuming only one sample column per raster

    # Extract only the sample column values in order
    sample_values = [feat[sample_column] for feat in features]

    # Append this column to UAG_ptv_sample using the folder name + sample prefix as column name
    UAG_ptv_sample[last_folder_name + "_" + column_prefix] = sample_values

    
# --- USER INPUTS ---
input_point_layer_path = r"D:\PLSCI 5200\Final_Project_GIS\Data\nyc_moua\nyc_moua.gpkg"
root_raster_folder = r"D:\PLSCI 5200\Final_Project_GIS\Data\air-quality\air_quality_NYCCAS\AnnAvg_1_15_300m\AnnAvg_1_15_300m"
target_crs_epsg = "EPSG:26918"  # Matching working model
column_prefix = "sample"
output_csv = r"D:\PLSCI 5200\Final_Project_GIS\sampled_points_output.csv"
# ---------------------

# Load the point layer
point_layer = QgsVectorLayer(input_point_layer_path, "UrbanAgSites", "ogr")
if not point_layer.isValid():
    print(f"❌ Could not load point layer: {input_point_layer_path}")
    exit()

print(f"✅ Input point layer loaded with {point_layer.featureCount()} points")

# Convert QgsFields to a list before slicing
all_fields = list(point_layer.fields())
base_columns = [field.name() for field in all_fields[:9]] + [field.name() for field in all_fields[-5:]]


UAG_ptv_sample = pd.DataFrame([
    [f[field] for field in base_columns]
    for f in point_layer.getFeatures()
], columns=base_columns)
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
# if all_samples:
#     final_df = UAG_ptv_sample
#     print("✅ All samples collected. Final DataFrame shape:", final_df.shape)

# Optional: Save to CSV
UAG_ptv_sample.to_csv(r"D:\PLSCI 5200\Final_Project_GIS\UAG_ptv_sample.csv", index=False)
print(f"📁 Saved output CSV to: {output_csv}")

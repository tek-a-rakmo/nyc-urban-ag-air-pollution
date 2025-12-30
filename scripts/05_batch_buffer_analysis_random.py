import os
import tempfile
import pandas as pd
import processing
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem)
    


# --- Function to process a single raster and return a DataFrame ---
def process_raster_points_buffer_zonal(raster_path, point_layer, target_crs, column_prefix, last_folder_name):
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

    # # --- Step 3: Raster Sampling ---
    # tmp_sampled_output = os.path.join(tempfile.gettempdir(), f"sampled_{last_folder_name}.gpkg")
    # sample_params = {
    #     'COLUMN_PREFIX': last_folder_name + "_" + column_prefix,
    #     'INPUT': reprojected_point_layer,
    #     'RASTERCOPY': tmp_raster_file,
    #     'OUTPUT': tmp_sampled_output
    # }
    # processing.run('native:rastersampling', sample_params)

    # --- Step 3: buffer_300m ---
    tmp_reprojected_vector_buffer_300m = os.path.join(tempfile.gettempdir(), f"reprojected_vector_buffer_{last_folder_name}.gpkg")

    buffer_params = {
        'DISSOLVE': False,
        'DISTANCE': 300,
        'END_CAP_STYLE': 0,  # Round
        'INPUT': reprojected_point_layer,
        'JOIN_STYLE': 0,  # Round
        'MITER_LIMIT': 2,
        'SEGMENTS': 30,
        'SEPARATE_DISJOINT': False,
        'OUTPUT': tmp_reprojected_vector_buffer_300m
    }
    processing.run('native:buffer', buffer_params)
    buffered_layer = QgsVectorLayer(tmp_reprojected_vector_buffer_300m, "buffer", "ogr")

    # --- Step 4: Zonal Statistics buffer ---
    if not buffered_layer.isValid():
        print("❌ buffer layer is invalid")
        return None
    tmp_buffer_zonal_stat = os.path.join(tempfile.gettempdir(), f"zonal_stat_buffer_{last_folder_name}.gpkg")
    
    zonal_params = {
        'COLUMN_PREFIX': last_folder_name + "_" + zonal_prefix,
        'INPUT': buffered_layer,
        'INPUT_RASTER': tmp_raster_file,
        'RASTER_BAND': 1,
        'STATISTICS': [2],  # Mean
        'OUTPUT': tmp_buffer_zonal_stat
    }
    processing.run('native:zonalstatisticsfb', zonal_params)
    



    # --- Step 5: Read Output into DataFrame ---
    buffer_zonal_layer = QgsVectorLayer(tmp_buffer_zonal_stat, "Zonal_Stat", "ogr")
    if not buffer_zonal_layer.isValid():
        print("❌ Zonal layer is invalid")
        return None

    features = buffer_zonal_layer.getFeatures()
    field_names = [field.name() for field in buffer_zonal_layer.fields()]

    # Find the sample column (the one that starts with the zonal_PREFIX(_buufer_mena)
    zonal_columns = [field for field in field_names if field.startswith(last_folder_name + "_" + zonal_prefix)]
    if not zonal_columns:
        print("❌ No zonal column found in layer")
        return None
    zonal_column = zonal_columns[0]  # assuming only one sample column per raster

    # Extract only the sample column values in order
    zonal_mean_values = [feat[zonal_column] for feat in features]

    # Append this column to UAG_ptv_sample using the folder name + sample prefix as column name
    Random_UAG_buffer_zonal[last_folder_name + "_" + zonal_prefix] = zonal_mean_values


    
#--- User Layer_Paths
random_points_path ='D:/PLSCI 5200/Final_Project_GIS/final_project_gis.gpkg|layername=nyc_moua_random_points'
root_raster_folder = r"D:\PLSCI 5200\Final_Project_GIS\Data\air-quality\air_quality_NYCCAS\AnnAvg_1_15_300m\AnnAvg_1_15_300m"
target_crs_epsg = "EPSG:26918"  # Matching working model
column_prefix = "random_sample"
zonal_prefix = "buffer_300m"
output_csv = r"D:\PLSCI 5200\Final_Project_GIS\Random_UAG_buffer_zonal.csv"
#---

#--- Initiate Vector Layer
random_nyc_moua_layer = QgsVectorLayer(random_points_path, "random_nyc_moua", "ogr")
if not random_nyc_moua_layer.isValid():
    print(f"❌ Could not load random point layer: {random_points_path}")
    exit()
print(f"✅ Input random_point layer loaded with {random_nyc_moua_layer.featureCount()} points")


# Convert QgsFields to a list before slicing
all_fields = list(random_nyc_moua_layer.fields())
base_columns = [field.name() for field in all_fields[:9]] + [field.name() for field in all_fields[-5:]]
#--- defining dataframe
Random_UAG_buffer_zonal = pd.DataFrame([
    [f[field] for field in base_columns]
    for f in random_nyc_moua_layer.getFeatures()
], columns=base_columns)
target_crs = QgsCoordinateReferenceSystem(target_crs_epsg)

# --- Loop through folders and collect samples ---
all_samples = []

for dirpath, dirnames, filenames in os.walk(root_raster_folder):
    if "hdr.adf" in filenames:
        raster_file_path = dirpath  # Use the directory directly for .adf rasters
        last_folder_name = os.path.basename(dirpath)
        df = process_raster_points_buffer_zonal(raster_file_path, random_nyc_moua_layer, target_crs, column_prefix, last_folder_name)
        if df is not None:
            all_samples.append(df)
            
            
# # Optional: Save to CSV
Random_UAG_buffer_zonal.to_csv(output_csv, index=False)
print(f"📁 Saved output CSV to: {output_csv}")


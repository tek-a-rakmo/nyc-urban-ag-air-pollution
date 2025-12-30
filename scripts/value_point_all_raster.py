import os
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsProcessing
import processing
import tempfile


# Function to process a single raster
def process_raster_sample_points(raster_path, point_layer, output_path, target_crs, column_prefix,last_folder_name):
    print(f"Processing raster: {raster_path}")

        # Load the raster layer
    raster_layer = QgsRasterLayer(raster_path, "PollutionRaster", "gdal")
    if not raster_layer.isValid():
        print(f"Raster path is NOT valid: {raster_path}")
        return  # Discard the path and exit the function
    else:
        print(f"Raster path is valid: {raster_path}")

    # Create temporary layer names
    import tempfile

# Create a temporary file path
    tmp_raster_file = os.path.join(tempfile.gettempdir(), f"reprojected_{os.path.basename(raster_path)}.tif")

    # reprojected_raster_uri = f"memory://reprojected_raster_{os.path.basename(raster_path)}"
    reprojected_points_uri = f"memory://reprojected_points"
    output_points_path = os.path.join(output_path, f"{os.path.splitext(os.path.basename(raster_path))[0]}__{last_folder_name}_sampled.geojson")

    # --- Step 1: Reproject Raster ---
    reproject_raster_params = {
        'INPUT': raster_path,
        'RESAMPLING':0,
        'TARGET_CRS': target_crs,
        'OUTPUT': tmp_raster_file
    }
    processing.run("gdal:warpreproject", reproject_raster_params)
    reprojected_raster_layer = QgsRasterLayer(reprojected_raster_uri, "ReprojectedRaster", "gdal")

    # --- Step 2: Reproject Points ---
    reproject_points_params = {
        'INPUT': point_layer,
        'TARGET_CRS': target_crs,
        'OUTPUT': reprojected_points_uri
    }
    processing.run('native:reprojectlayer', reproject_points_params)
    reprojected_point_layer = QgsVectorLayer(reprojected_points_uri, "ReprojectedPoints", "memory")

    # --- Step 3: Sample Raster Values ---
    sample_params = {
        'COLUMN_PREFIX': last_folder_name + column_prefix,
        'INPUT': reprojected_point_layer,
        'RASTERCOPY': reprojected_raster_layer,
        'OUTPUT': output_points_path
    }
    processing.run('native:rastersampling', sample_params)
    print(f"  Output saved to: {output_points_path}")


# --- USER INPUTS ---
input_point_layer_path = r"D:\PLSCI 5200\Final_Project_GIS\Data\nyc_moua\nyc_moua.gpkg"
root_raster_folder = r"D:\PLSCI 5200\Final_Project_GIS\Data\air-quality\air_quality_NYCCAS\AnnAvg_1_15_300m\AnnAvg_1_15_300m"
output_folder = r"D:\PLSCI 5200\Final_Project_GIS\QGIS_model_output"
target_crs_epsg = "EPSG:26918"
raster_file_extension = ".adf"  # Or whatever your raster file extension is
column_prefix = "sample"
# ---------------------

# Load the point layer
point_layer = QgsVectorLayer(input_point_layer_path, "UrbanAgSites", "ogr")
if not point_layer.isValid():
    print(f"Error: Could not load point layer: {input_point_layer_path}")
    exit()

# Define the target CRS
target_crs = QgsCoordinateReferenceSystem(target_crs_epsg)


# raster_path_trial = r"D:\PLSCI 5200\Final_Project_GIS\Data\air-quality\air_quality_NYCCAS\AnnAvg_1_15_300m\AnnAvg_1_15_300m\aa10_bc300m\hdr.adf"
# process_raster_sample_points(raster_path_trial, point_layer, output_folder, target_crs, column_prefix,last_folder_name)


# Walk through the root folder and its subdirectories
for dirpath, dirnames, filenames in os.walk(root_raster_folder):
    if "hdr.adf" in filenames:
        raster_file_path = dirpath  # Use the directory itself
        last_folder_name = os.path.basename(dirpath)
        process_raster_sample_points(raster_file_path, point_layer, output_folder, target_crs, column_prefix, last_folder_name)


print("Processing complete.")
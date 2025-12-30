from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsPointLocator, QgsFeature, QgsField, QgsFields, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry
from qgis.PyQt.QtCore import QVariant

# --- USER INPUTS ---
point_layer_name = "nyc_moua"  # Replace with the actual name of your point layer
raster_layer_name = "aa1_bc300m"  # Replace with the actual name of your raster layer
output_field_name = "air_quality_points_aa1_bc"  # Name for the new field in the point layer
# ---------------------

# Get the point layer
point_layer = QgsProject.instance().mapLayer(point_layer_name)
if not point_layer or point_layer.type() != QgsVectorLayer.Point:
    print(f"Error: Point layer '{point_layer_name}' not found or is not a point layer.")
    exit()

# Get the raster layer
raster_layer = QgsProject.instance().mapLayer(raster_layer_name)
if not raster_layer or raster_layer.type() != QgsRasterLayer.Raster:
    print(f"Error: Raster layer '{raster_layer_name}' not found or is not a raster layer.")
    exit()

# Ensure the raster layer is loaded and has valid extent
if not raster_layer.isValid():
    print(f"Error: Raster layer '{raster_layer_name}' is not valid.")
    exit()

# Get the CRS of both layers
point_crs = point_layer.crs()
raster_crs = raster_layer.crs()

# Create a coordinate transform context if CRSs are different
transform_context = None
if point_crs != raster_crs:
    transform_context = QgsCoordinateTransformContext(point_crs, raster_crs, QgsProject.instance())
    print("Warning: Point layer and raster layer have different Coordinate Reference Systems. Points will be transformed to the raster's CRS for value extraction.")

# Create a data provider for the raster
provider = raster_layer.dataProvider()
if not provider:
    print(f"Error: Could not access data provider for raster layer '{raster_layer_name}'.")
    exit()

# Add a new field to the point layer to store the raster values
point_layer.startEditing()
point_layer.addAttribute(QgsField(output_field_name, QVariant.Double))  # Assuming air quality values are numeric
point_layer.updateFields()

# Get the index of the newly added field
field_index = point_layer.fields().lookupField(output_field_name)

# Iterate through each point feature and extract the raster value
request = QgsRaster.PixelValueRequest()
for feature in point_layer.getFeatures():
    geom = feature.geometry()
    if geom and geom.type() == QgsGeometry.Point:
        point = geom.asPoint()

        # Transform the point coordinates to the raster's CRS if necessary
        if transform_context:
            transformed_point = transform_context.transform(point)
        else:
            transformed_point = point

        # Get the raster value at the transformed point's coordinates
        results = provider.identify(transformed_point, QgsRaster.IdentifyFormatValue)
        if results.isValid():
            # Assuming your raster has only one band.
            raster_value = results.results(1) if 1 in results.results() else None
            if raster_value is not None:
                point_layer.changeAttributeValue(feature.id(), field_index, raster_value)
            else:
                print(f"Warning: No raster value found at point {feature.id()} after transformation.")
        else:
            print(f"Warning: Could not identify raster value at point {feature.id()} after transformation.")
    else:
        print(f"Warning: Feature {feature.id()} is not a point geometry.")

point_layer.commitChanges()
point_layer.updateFeature(feature) # Ensure the attribute table reflects the changes

print(f"Raster values from '{raster_layer_name}' (CRS: {raster_crs.authId()}) have been added to the '{output_field_name}' field in '{point_layer_name}' (CRS: {point_crs.authId()}). Points were transformed if their CRS differed.")
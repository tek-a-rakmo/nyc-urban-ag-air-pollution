# NYC Urban Agriculture Air Pollution Project

## Overview
This project analyzes air pollution in relation to urban agriculture in New York City. It uses PyQGIS to process spatial data, extract raster values (e.g., PM2.5, NO2) at specific points (urban gardens), and generate statistical summaries.

## Repository Structure
- `data/`: Contains raw and processed spatial data.
    - `raw/`: Original datasets (not tracked in git if large).
    - `processed/`: Intermediate layers and outputs.
- `scripts/`: Python scripts for QGIS (PyQGIS).
- `models/`: QGIS processing models (`.model3`).
- `qgis_project/`: The main QGIS project file (`.qgz`).
- `outputs/`: Generated figures and tables.
- `docs/`: Project reports and references.

## Getting Started

### Prerequisites
- **QGIS**: This project works best with QGIS 3.x (LTR recommended).
- **Plugins**: Ensure standard processing plugins are enabled.

### Setup
1. Clone this repository.
2. Download the required large datasets (see Data Access below).
3. Place the data in `data/raw/`.
4. Open the `.qgz` project file in `qgis_project/`.

### Running the Analysis
The analysis is strictly PyQGIS-based. You can run the scripts from the QGIS Python Console or the Processing Toolbox.

**Script Order:**
1. `scripts/01_extract_values.py`: Extracts raster values to points.
2. `...` (Add other scripts here)

## Data Access
Large files (Geopackages, TIFFs) are not included in this repository.
- **Source 1**: [Link to Source]
- **Source 2**: [Link to Source]

## Authors
- Omkar

## License
[License Name]

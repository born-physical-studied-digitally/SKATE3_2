# Seismogram Pipeline

SKATE is an open-source prototy[e software tool, originally developed by Andrew Bartlett et. al. using Python 2, with funding from the AFRL. From a high-resolution image of a legacy seismogram, SKATE produces a GeoJSON file with groups of coordinates of pixels identified as belonging to the recorded waveforms. These groups of coordinates are called segments. This repository contains SKATE 3, a Python 3 version of the original SKATE software (originally converted by Brian Kim), and it is meant to further improve SKATE's ability to digitize scanned paper seismogram data. This improvement work is funded by the National Science Foundation, award [#2410335](https://www.nsf.gov/awardsearch/show-award?AWD_ID=2410335).

## Installation

### Prerequisites

- Python 3.7 or higher
- Anaconda (recommended for dependency management)

### Install Dependencies

```bash
# Install core dependencies
pip install numpy scipy scikit-image matplotlib geojson docopt imageio

# Or install from environment file
conda env create -f environment.yaml
```

### Install the Package

```bash
# Install in development mode
pip install -e .

# Or install directly
pip install .
```

## Project Structure

```
seismogram-pipeline/
├── src/
│   └── seismogram_pipeline/          # Main package
│       ├── __init__.py
│       ├── core/                     # Core processing modules
│       │   ├── __init__.py
│       │   ├── roi_detection.py      # Region of interest detection
│       │   ├── meanline_detection.py # Meanline detection
│       │   ├── intersection_detection.py # Intersection detection
│       │   ├── trace_segmentation.py # Trace segmentation
│       │   ├── segment_assignment.py # Segment assignment
│       │   ├── endpoints.py          # Endpoint detection
│       │   └── ...                   # Other core modules
│       ├── cli/                      # Command-line interface
│       │   ├── __init__.py
│       │   ├── get_all_metadata.py   # Main pipeline script
│       │   ├── get_roi.py            # ROI detection CLI
│       │   ├── get_meanlines.py      # Meanline detection CLI
│       │   └── ...                   # Other CLI scripts
│       ├── utils/                    # Utility functions
│       └── models/                   # Data models
├── scripts/                          # Standalone scripts
│   ├── queue/                        # Queue management tools
│   └── deployment/                   # Deployment scripts
├── data/                             # Data files
│   ├── inputs/                       # Sample input files
│   ├── outputs/                      # Output examples
│   └── examples/                     # Example data
├── tests/                            # Test files
├── docs/                             # Documentation
├── config/                           # Configuration files
└── README.md                         # This file
```

## Usage

### Command Line Interface

The package provides several command-line tools for processing seismogram images:

#### Process Complete Pipeline

```bash
# Generate all metadata for a seismogram
seismogram-get-all-metadata --image input.png --output output_dir --scale 0.25
```

#### Individual Processing Steps

```bash
# Detect region of interest
seismogram-get-roi --image input.png --output roi.json --scale 0.25

# Detect meanlines
seismogram-get-meanlines --image input.png --roi roi.json --output meanlines.json

# Detect intersections
seismogram-get-intersections --image input.png --roi roi.json --output intersections.json

# Detect segments
seismogram-get-segments --image input.png --roi roi.json --output segments.json

# Assign segments to meanlines
seismogram-get-segment-assignments --segments segments.json --meanlines meanlines.json --output assignments.json

# Extract endpoints
seismogram-get-endpoints --segments segments.json --output endpoints.json
```

#### Utility Tools

```bash
# Resize image
seismogram-resize-image --image input.png --scale 0.25 --output resized.png

# Create thresholded image
seismogram-get-thresholded-image --image input.png --output thresholded.png
```

### Python API

You can also use the package programmatically:

```python
from seismogram_pipeline import get_roi, detect_meanlines, find_intersections

# Load and process image
import numpy as np
from skimage import io

image = io.imread('seismogram.png', as_gray=True)

# Detect ROI
roi_corners = get_roi(image, scale=0.25)
roi_geojson = corners_to_geojson(roi_corners)

# Detect meanlines
meanlines = detect_meanlines(image, roi_corners, scale=0.25)
meanlines_geojson = meanlines_to_geojson(meanlines)

# Detect intersections
intersections = find_intersections(image, roi_corners)
```

## Output Format

The pipeline generates several types of output:

- **ROI (Region of Interest)**: GeoJSON polygon defining the area of interest
- **Meanlines**: GeoJSON LineString features representing the main signal lines
- **Intersections**: GeoJSON Point features with radius properties
- **Segments**: GeoJSON LineString features representing individual signal segments
- **Segment Assignments**: JSON mapping segments to meanlines
- **Endpoints**: GeoJSON Point features representing segment endpoints

## Configuration

The pipeline supports various parameters for tuning the processing:

- `--scale`: Scale factor for processing (0.25 for quarter-size, 1.0 for full-size)
- `--debug`: Directory to save intermediate processing images
- `--stats`: File to save processing statistics

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/
```

### Code Style

```bash
# Format code
black src/

# Lint code
flake8 src/
```

## Queue Processing

For batch processing of multiple seismograms, the package includes queue management tools:

```bash
# Prepare queue with files
node scripts/queue/prepare_queue.js

# Process queue
node scripts/queue/process_queue.js
```

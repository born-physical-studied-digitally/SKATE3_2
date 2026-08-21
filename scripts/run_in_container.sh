#!/usr/bin/env bash
set -e

# Get the absolute path of the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 
# point PROJECT_ROOT to the main repository folder:
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)" 

# Automatically detect user container engine 
if command -v podman &> /dev/null; then
    ENGINE="podman"
    VOL_SUFFIX=":z"
    IMAGE="localhost/seismogram-pipeline"
else
    ENGINE="docker"
    VOL_SUFFIX=""
    IMAGE="seismogram-pipeline"
fi

echo "==> Using container engine: $ENGINE"

# Ensure data directories exist relative to the project root
mkdir -p "$PROJECT_ROOT/data/inputs" "$PROJECT_ROOT/data/outputs"

# Run the container using absolute paths for safety
$ENGINE run --rm \
  -v "$PROJECT_ROOT/data/inputs:/app/data/inputs$VOL_SUFFIX" \
  -v "$PROJECT_ROOT/data/outputs:/app/data/outputs$VOL_SUFFIX" \
  "$IMAGE" "$@"

# Example usage:
# ./scripts/run_in_container.sh --image /app/data/inputs/COL_75_06_16_1706_LHZ.png --output /app/data/outputs/ --scale 0.25
# ./scripts/run_in_container.sh seismogram-get-roi --image /app/data/inputs/COL_75_06_16_1706_LHZ.png --output /app/data/outputs/roi.json --scale 0.25

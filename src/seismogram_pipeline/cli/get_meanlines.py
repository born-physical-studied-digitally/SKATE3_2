"""
Description:
  Given a grayscale seismogram and a geojson Polygon feature
  representing the seismogram's region-of-interest, estimates
  the meanlines of the seismogram data, and saves as a geojson
  FeatureCollection of features with LineString geometries.

Usage:
  get_meanlines.py --roi <filename> --image <filename> --output <filename> [--scale <scale>] [--debug <directory>]
  get_meanlines.py -h | --help

Options:
  -h --help            Show this screen.
  --roi <filename>     Filename of geojson Polygon representing region-of-interest.
  --image <filename>   Filename of grayscale seismogram.
  --output <filename>  Filename of geojson output.
  --scale <scale>      1 for a full-size seismogram, 0.25 for quarter-size, etc. [default: 1]
  --debug <directory>  Save intermediate steps as images for inspection in <directory>.

"""

import os, yaml
from docopt import docopt
from typing import Union


def get_meanlines(
  in_file: str,
  out_file: str,
  roi_file: str,
  scale: float = 1,
  debug_dir: Union[str, bool] = False,
) -> None:
  """
  Process grayscale image and region of interest and write meanlines

  Parameters
  ----------
  in_file: str
      Input grayscale seismogram file path
  out_file: str
      Output geojson file path
  roi_file: str
      Region of interest geojson file path
  scale: float, default 1
      Image scale factor
  debug_dir: str | bool, default False
      Flag whether to save intermediate images
  """

  CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../config.json")
  )

  with open(CONFIG_PATH, "r") as f:
    storage_config = yaml.safe_load(f)["storage"]

  if isinstance(debug_dir, str):
    from ..core.dir import ensure_dir_exists

    ensure_dir_exists(debug_dir)

  from ..core.debug import Debug

  if isinstance(debug_dir, str):
    Debug.set_directory(debug_dir)

  from ..core.timer import timeStart, timeEnd
  from ..core.load_image import get_image
  from ..core.geojson_io import get_features, save_features
  from ..core.polygon_mask import mask_image
  from ..core.meanline_detection import detect_meanlines, meanlines_to_geojson

  timeStart("get meanlines")

  timeStart("read image")
  image = get_image(in_file)
  timeEnd("read image")

  roi_polygon = get_features(roi_file)["geometry"]["coordinates"][0]

  timeStart("mask image")
  masked_image = mask_image(image, roi_polygon)
  timeEnd("mask image")

  meanlines = detect_meanlines(masked_image, scale=scale)

  timeStart("convert to geojson")
  meanlines_as_geojson = meanlines_to_geojson(meanlines)
  timeEnd("convert to geojson")

  # config default fallback
  if not out_file:
    out_file = os.path.join(
      storage_config.get("outputs_dir", "data/outputs"),
      storage_config["pipeline_outputs"]["meanlines"],
    )

  timeStart("saving as geojson")
  save_features(meanlines_as_geojson, out_file)
  timeEnd("saving as geojson")

  timeEnd("get meanlines")


def main():
    """Main entry point for the get_meanlines CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    roi_file = arguments["--roi"]
    out_file = arguments["--output"]
    scale = float(arguments["--scale"])
    debug_dir = arguments["--debug"]

    if in_file and roi_file:
        get_meanlines(in_file, out_file, roi_file, scale, debug_dir)
    else:
        print(arguments)


if __name__ == '__main__':
    main()

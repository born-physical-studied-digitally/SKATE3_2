"""
Description:
  Calculates the corners of the region of interest in a grayscale
  seismogram image.

Usage:
  get_roi.py --image <filename> [--output <filename>] [--scale <scale>] [--debug <directory>]
  get_roi.py -h | --help

Options:
  -h --help            Show this screen.
  --image <filename>   Filename of grayscale input image.
  --output <filename>  Filename of geojson output.
  --scale <scale>      1 for a full-size seismogram, 0.25 for quarter-size, etc. [default: 1]
  --debug <directory>  Save intermediate steps as images for inspection in <directory>.

"""

from docopt import docopt
from typing import Union
import imageio.v2 as imageio
import os


def get_roi(
  in_file: str, out_file: str, scale: float = 1, debug_dir: Union[str, bool] = False
) -> None:
  """
  Process grayscale image and write region of interest

  Parameters
  ----------
  in_file: str
      Grayscale seismogram image file path
  out_file: str
      Output file path
  scale: int, default 1 (unused)
      Image scale factor
  debug_dir: str | bool, default False
      Flag whether to save intermediate images
  """

  if isinstance(debug_dir, str):
    from ..core.dir import ensure_dir_exists

    ensure_dir_exists(debug_dir)

  from ..core.timer import timeStart, timeEnd
  from ..core.load_image import get_image
  from ..core.roi_detection import get_roi, corners_to_geojson
  from ..core.geojson_io import save_features

  timeStart("ROI")

  timeStart("read image")
  image = get_image(in_file)
  timeEnd("read image")

  corners = get_roi(image, scale=scale)

  timeStart("convert to geojson")
  corners_as_geojson = corners_to_geojson(corners)
  timeEnd("convert to geojson")

  if isinstance(debug_dir, str):
    from ..core.polygon_mask import mask_image
    from scipy import misc

    roi_polygon = corners_as_geojson["geometry"]["coordinates"][0]
    timeStart("mask image")
    masked_image = mask_image(image, roi_polygon)
    timeEnd("mask image")
    imageio.imwrite(os.join(debug_dir, "/masked_image.png"), masked_image.filled(0))

  if out_file:
    timeStart("saving as geojson")
    save_features(corners_as_geojson, out_file)
    timeEnd("saving as geojson")
  else:
    print(corners_as_geojson)

  timeEnd("ROI")


def main():
    """Main entry point for the get_roi CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    out_file = arguments["--output"]
    scale = float(arguments["--scale"])
    debug_dir = arguments["--debug"]

    if in_file:
        get_roi(in_file, out_file, scale, debug_dir)
    else:
        print(arguments)


if __name__ == '__main__':
    main()

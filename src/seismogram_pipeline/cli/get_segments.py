"""
Description:
  Calculates the segments in a grayscale seismogram image.

Usage:
  get_segments.py --image <filename> --roi <filename> [--output <filename>] [--scale <scale>] [--debug <directory>]
  get_segments.py -h | --help

Options:
  -h --help            Show this screen.
  --image <filename>   Filename of grayscale input image.
  --roi <filename>     Filename of geojson roi.
  --output <filename>  Filename of geojson output.
  --scale <scale>      1 for a full-size seismogram, 0.25 for quarter-size, etc. [default: 1]
  --debug <directory>  Save intermediate steps as images for inspection in <directory>.

"""

from docopt import docopt
from typing import Union


def get_segments(
  in_file: str,
  roi_file: str,
  out_file: str,
  scale: int = 1,
  debug_dir: Union[str, bool] = False,
) -> None:
  """
  Process grayscale image & region of interest and write segments

  Parameters
  ----------
  in_file: str
      Grayscale seismogram image file path
  roi_file: str
      Region of interest geojson file path
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
  from ..core.geojson_io import get_features
  from ..core.segment_detection import get_segments
  from ..core.segment_detection import save_segments_as_geojson

  timeStart("get segments")

  timeStart("read image")
  image = get_image(in_file)
  timeEnd("read image")

  intersections = get_features(roi_file)

  timeStart("calculate segments")
  segments = get_segments(image, intersections)
  timeEnd("calculate segments")

  save_segments_as_geojson(segments, out_file)
  timeEnd("get segments")


def main():
    """Main entry point for the get_segments CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    roi_file = arguments["--roi"]
    out_file = arguments["--output"]
    scale = float(arguments["--scale"]) if arguments["--scale"] else 1
    debug_dir = arguments["--debug"]

    if in_file and out_file and roi_file:
        get_segments(in_file, roi_file, out_file, scale, debug_dir)
    else:
        print(arguments)


if __name__ == '__main__':
    main()

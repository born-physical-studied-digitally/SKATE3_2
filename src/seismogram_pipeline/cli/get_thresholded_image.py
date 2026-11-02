"""
Description:
  Creates a thresholded image from a grayscale seismogram.

Usage:
  get_thresholded_image.py --image <filename> [--output <filename>] [--debug <directory>]
  get_thresholded_image.py -h | --help

Options:
  -h --help            Show this screen.
  --image <filename>   Filename of grayscale input image.
  --output <filename>  Filename of output image.
  --debug <directory>  Save intermediate steps as images for inspection in <directory>.

"""

from docopt import docopt
from typing import Union


def get_thresholded_image(
  in_file: str, out_file: str, debug_dir: Union[str, bool] = False
) -> None:
  """
  Process grayscale image and writes threshold image

  in_file: str
      Grayscale seismogram image file path
  out_file: str
      Output image file path
  debug_dir: str | bool, default False
      Flag whether to save intermediate images
  """

  if isinstance(debug_dir, str):
    from ..core.dir import ensure_dir_exists

    ensure_dir_exists(debug_dir)

  from ..core.timer import timeStart, timeEnd
  from ..core.otsu_threshold_image import otsu_threshold_image
  from ..core.load_image import get_image
  from scipy import misc

  timeStart("read image")
  grayscale_image = get_image(in_file)
  timeEnd("read image")

  timeStart("threshold image")
  thresholded_image = otsu_threshold_image(grayscale_image)
  timeEnd("threshold image")

  timeStart("save image")
  misc.imsave(out_file, thresholded_image)
  timeEnd("save image")


def main():
    """Main entry point for the get_thresholded_image CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    out_file = arguments["--output"]
    debug_dir = arguments["--debug"]

    if in_file:
        get_thresholded_image(in_file, out_file, debug_dir)
    else:
        print(arguments)


if __name__ == '__main__':
    main()

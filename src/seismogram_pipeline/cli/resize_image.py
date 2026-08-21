"""
Description:
  Resizes an image to a specified scale.

Usage:
  resize_image.py --image <filename> --scale <scale> [--output <filename>]
  resize_image.py -h | --help

Options:
  -h --help            Show this screen.
  --image <filename>   Filename of input image.
  --scale <scale>      Scale factor (e.g., 0.25 for quarter size).
  --output <filename>  Filename of output image.

"""

from docopt import docopt
from skimage.transform import resize
import imageio


def resize_image(in_file: str, scale: float, out_file: str) -> None:
  """
  Process input image and save resized image

  Parameters
  ----------
  in_file: str
      Grayscale  image file path
  out_file: str
      Output image file path
  debug_dir: str | bool, default False
      Flag whether to save intermediate images
  """

  from ..core.load_image import get_image
  from ..core.timer import timeStart, timeEnd

  timeStart("load image")
  image = get_image(in_file)
  timeEnd("load image")

  timeStart("resize image")
  new_shape = (int(image.shape[0] * scale), int(image.shape[1] * scale))
  resized = resize(image, new_shape, preserve_range=True, anti_aliasing=True).astype(
    image.dtype
  )
  timeEnd("resize image")

  if out_file:
    timeStart("save image")
    imageio.imwrite(out_file, resized)
    timeEnd("save image")
  else:
    print("No output file specified.")


def main():
    """Main entry point for the resize_image CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    scale = float(arguments["--scale"])
    out_file = arguments["--output"]

    if in_file and scale:
        resize_image(in_file, scale, out_file)
    else:
        print(arguments)


if __name__ == '__main__':
    main()

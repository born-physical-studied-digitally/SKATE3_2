# -*- coding: utf-8 -*-
"""
Description:
  Generate all metadata (ROI, meanlines, intersections, and segments as of 6/10/2015)
  for a single seismogram.

Usage:
  pipeline.py --image <filename> --output <directory> [--stats <filename>] [--scale <scale>] [--debug <directory>] [--fix-seed]
  pipeline.py -h | --help

Options:
  -h --help             Show this screen.
  --image <filename>    Filename of seismogram.
  --output <directory>  Save metadata in <directory>.
  --stats <filename>    Write statistics (e.g. number of meanlines, size of ROI) to <filename>.
                        If <filename> already exists, stats will be appended, not overwritten.
  --scale <scale>       1 for a full-size seismogram, 0.25 for quarter-size, etc. [default: 1]
  --debug <directory>   Save intermediate steps as images for inspection in <directory>.
  --fix-seed            Fix random seed.

"""

from docopt import docopt
import imageio.v2 as imageio
from typing import Union


def analyze_image(
  in_file: str,
  out_dir: str,
  stats_file: bool = False,
  scale: float = 1,
  debug_dir: Union[str, bool] = False,
  fix_seed: bool = False,
) -> None:
  """
  Process seismogram image and write statistics & metadata

  Parameters
  ----------
  in_file: str
      Input image file path
  out_dir: str
      Output metadata file path
  stats_file: str
      Ouput statistics file path
  scale: float, default 1
      Image resize scale
  debug_dir: str | bool, default False
      Flag whether to save intermediate images
  fix_seed: bool, default False
      Flag whether to run with fixed seed
  """

  from ..core.dir import ensure_dir_exists
  from ..core.debug import Debug
  from ..core.stats_recorder import Record

  if debug_dir:
    Debug.set_directory(debug_dir)

  if fix_seed:
    Debug.set_seed(1234567890)

  if stats_file:
    Record.activate()

  ensure_dir_exists(out_dir)

  from ..core.timer import timeStart, timeEnd

  from ..core.load_image import get_grayscale_image, image_as_float
  from skimage.morphology import medial_axis
  from ..core.roi_detection import get_roi, corners_to_geojson
  from ..core.polygon_mask import mask_image
  from ..core.meanline_detection import detect_meanlines, meanlines_to_geojson
  from ..core.threshold import flatten_background
  from ..core.ridge_detection import find_ridges
  from ..core.binarization import binary_image
  from ..core.intersection_detection import find_intersections
  from ..core.trace_segmentation import get_segments, segments_to_geojson
  from ..core.geojson_io import save_features, save_json
  from ..core.utilities import encode_labeled_image_as_rgb
  from scipy import misc
  import numpy as np
  import os
  import yaml

  # Load complete config file
  CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../config.yaml")
  )
  with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

  storage_config = config["storage"]
  output_filenames = storage_config["pipeline_outputs"]
  settings = config["pipeline_settings"]

  # use file directories instead of hardcoded strings
  paths = {
    "roi": os.path.join(out_dir, output_filenames["roi"]),
    "meanlines": os.path.join(out_dir, output_filenames["meanlines"]),
    "intersections": os.path.join(out_dir, output_filenames["intersections"]),
    "intersections_raster": os.path.join(
      out_dir, output_filenames["intersections_raster"]
    ),
    "segments": os.path.join(out_dir, output_filenames["segments"]),
    "segment_regions": os.path.join(out_dir, output_filenames["segment_regions"]),
    "segment_assignments": os.path.join(
      out_dir, output_filenames["segment_assignments"]
    ),
  }

  timeStart("get all metadata")

  timeStart("read image")
  img_gray = image_as_float(get_grayscale_image(in_file))
  timeEnd("read image")

  print("\n--ROI--")
  timeStart("get region of interest")
  corners = get_roi(img_gray, scale=scale, config=settings.get("roi_detection"))
  timeEnd("get region of interest")

  timeStart("convert roi to geojson")
  corners_as_geojson = corners_to_geojson(corners)
  timeEnd("convert roi to geojson")

  timeStart("saving roi as geojson")
  save_features(corners_as_geojson, paths["roi"])
  timeEnd("saving roi as geojson")

  print("\n--MASK IMAGE--")
  roi_polygon = corners_as_geojson["geometry"]["coordinates"][0]

  timeStart("mask image")
  masked_image = mask_image(img_gray, roi_polygon)
  timeEnd("mask image")

  Debug.save_image("main", "masked_image", masked_image.filled(0))

  image_processing = settings["image_processing"]
  max_val = image_processing["max_intensity"]
  bin_count = image_processing["histogram_bins"]

  if Record.active:
    non_masked_values = max_val * masked_image.compressed()
    bins = np.arange(bin_count)
    image_hist, _ = np.histogram(non_masked_values, bins=bins)
    Record.record("roi_intensity_hist", image_hist.tolist())

  print("\n--MEANLINES--")
  meanlines = detect_meanlines(
    masked_image, corners, scale=scale, config=settings.get("meanline_detection")
  )

  timeStart("convert meanlines to geojson")
  meanlines_as_geojson = meanlines_to_geojson(meanlines)
  timeEnd("convert meanlines to geojson")

  timeStart("saving meanlines as geojson")
  save_features(meanlines_as_geojson, paths["meanlines"])
  timeEnd("saving meanlines as geojson")

  min_prob_threshold = image_processing["min_prob_threshold"]
  print("\n--FLATTEN BACKGROUND--")
  img_dark_removed, background = flatten_background(
    masked_image,
    prob_background=min_prob_threshold,
    return_background=True,
    img_gray=img_gray,
  )

  Debug.save_image("main", "flattened_background", img_dark_removed)

  masked_image = None

  print("\n--RIDGES--")
  timeStart("get horizontal and vertical ridges")
  ridges_h, ridges_v = find_ridges(img_dark_removed, background)
  ridges = ridges_h | ridges_v
  timeEnd("get horizontal and vertical ridges")

  print("\n--THRESHOLDING--")
  timeStart("get binary image")
  img_bin = binary_image(
    img_dark_removed, markers_trace=ridges, markers_background=background
  )
  timeEnd("get binary image")

  img_dark_removed = None
  background = None

  print("\n--SKELETONIZE--")
  timeStart("get medial axis skeleton and distance transform")
  img_skel, dist = medial_axis(img_bin, return_distance=True)
  timeEnd("get medial axis skeleton and distance transform")

  Debug.save_image("skeletonize", "skeleton", img_skel)

  print("\n--INTERSECTIONS--")
  intersections = find_intersections(img_bin, img_skel, dist, figure=False)

  timeStart("convert to geojson")
  intersection_json = intersections.asGeoJSON()
  timeEnd("convert to geojson")

  timeStart("saving intersections as geojson")
  save_features(intersection_json, paths["intersections"])
  timeEnd("saving intersections as geojson")

  timeStart("convert to image")
  intersection_image = intersections.asImage() 
  timeEnd("convert to image")

  Debug.save_image("intersections", "intersections", intersection_image)
  timeStart("save intersections raster")
  intersection_image = np.array(intersection_image)
  if not np.issubdtype(intersection_image.dtype, np.number):
    print(f"WARNING: image dtype is {intersection_image.dtype}, converting to uint8")
    intersection_image = intersection_image.astype(np.uint8)
  # misc.imsave(paths["intersections_raster"], intersection_image)
  imageio.imwrite(paths["intersections_raster"], intersection_image)
  timeEnd("save intersections raster")

  print("\n--SEGMENTS--")
  timeStart("get segments")
  segments, labeled_regions = get_segments(
    img_gray,
    img_bin,
    img_skel,
    dist,
    intersection_image,
    ridges_h,
    ridges_v,
    figure=True,
  )
  timeEnd("get segments")

  timeStart("encode labels as rgb values")
  rgb_segments = encode_labeled_image_as_rgb(labeled_regions)
  timeEnd("encode labels as rgb values")

  rgb_segments = np.array(rgb_segments)  # ensure NumPy array
  if rgb_segments.dtype != np.uint8:
      print(f"Converting segment image from {rgb_segments.dtype} to uint8")
      rgb_segments = (rgb_segments * max_val).clip(0, max_val).astype(np.uint8)

  timeStart("save segment regions")
  # misc.imsave(paths["segment_regions"], rgb_segments) # deprecated
  imageio.imwrite(paths["segment_regions"], rgb_segments)
  timeEnd("save segment regions")

  timeStart("convert centerlines to geojson")
  segments_as_geojson = segments_to_geojson(segments)
  timeEnd("convert centerlines to geojson")

  timeStart("saving centerlines as geojson")
  save_features(segments_as_geojson, paths["segments"])
  timeEnd("saving centerlines as geojson")

  # TODO: fix the return logic below
  # return (img_gray, ridges, img_bin, intersections, img_seg)
  # return segments
  # detect center lines

  # connect segments

  # output data

  time_elapsed = timeEnd("get all metadata")

  Record.record("time_elapsed", float("%.2f" % time_elapsed))

  if stats_file:
    Record.export_as_json(stats_file)

  # TODO: refactor this into some sort of status module.
  # For now, since this is our only problematic status,
  # it's hard to know what to generalize. Eventually
  # we might want to flag several different statuses
  # for specific conditions.
  max_segments_reasonable = image_processing["max_segments_reasonable"]
  if len(segments) > max_segments_reasonable:
    print("STATUS>>>problematic<<<")
  else:
    print("STATUS>>>complete<<<")


def main():
    """Main entry point for the get_all_metadata CLI."""
    arguments = docopt(__doc__)
    in_file = arguments["--image"]
    out_dir = arguments["--output"]
    stats_file = arguments["--stats"]
    scale = float(arguments["--scale"])
    debug_dir = arguments["--debug"]
    fix_seed = arguments["--fix-seed"]

    if in_file and out_dir:
        analyze_image(in_file, out_dir, stats_file, scale, debug_dir, fix_seed)
    else:
        print(arguments)


if __name__ == '__main__':
    main()

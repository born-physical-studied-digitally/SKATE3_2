# -*- coding: utf-8 -*-
"""
Description:
  Assigns segments to meanlines in a seismogram.

Usage:
  get_segment_assignments.py --segments <filename> --meanlines <filename> [--output <filename>]
  get_segment_assignments.py -h | --help

Options:
  -h --help              Show this screen.
  --segments <filename>  Filename of geojson segments.
  --meanlines <filename> Filename of geojson meanlines.
  --output <filename>    Filename of json output.

"""

from docopt import docopt


def get_segment_assignments(
  segments_file: str, meanlines_file: str, out_file: str
) -> None:
  """
  Process the segments and meanlines files to extract and write segment assignments

  Parameters
  ----------
  segments_file: str
      Input segments file path
  meanlines_file: str
      Input meanlines file path
  out_file: str
      Output segment assignments file path
  """

  from ..core.geojson_io import get_features
  from ..core.timer import timeStart, timeEnd
  from ..core.segment_assignment import (
    assign_segments_to_meanlines,
    save_assignments_as_json
  )

  timeStart("get segment assignments")

  timeStart("read segments")
  segments_features = get_features(filename=segments_file)
  timeEnd("read segments")

  timeStart("read meanlines")
  meanlines_features = get_features(filename=meanlines_file)
  timeEnd("read meanlines")

  # assign segments to their associated meanlines
  timeStart("segment assignment")
  assignments = assign_segments_to_meanlines(
    segments=segments_features,
    meanlines=meanlines_features,
    segment_data=segments_features,  # NOTE: `segments_features` passed twice (inferred from function behavior)
  )
  timeEnd("segment assignment")

  # save to output JSON file
  save_assignments_as_json(data=assignments, filepath=out_file)

  timeEnd("get segment assignments")


def main():
    """Main entry point for the get_segment_assignments CLI."""
    arguments = docopt(__doc__)
    segments_file = arguments["--segments"]
    meanlines_file = arguments["--meanlines"]
    out_file = arguments["--output"]

    if segments_file and meanlines_file:
        get_segment_assignments(segments_file, meanlines_file, out_file)
    else:
        print(arguments)


if __name__ == '__main__':
    main()

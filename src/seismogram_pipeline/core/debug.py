"""
Debug utilities for image exporting and seed management in the seismogram pipeline.
"""
from .dir import ensure_dir_exists
from pathlib import Path
from numpy.random import RandomState
from imageio.v3 import imwrite
import numpy.typing as npt
from typing import Any, Optional

def pad(number: int) -> str:
  """
  Pads single digit numbers with a leading 0

  Parameters
  ----------
  number : int
      Nonnegative integer

  Returns
  -------
  numstr : str
      String representation of an int, zero-padded if < 10
  """
  return f"{number:02d}" # switched to f-string implementation 

class Debug:
  """
  Class-level util for tracking pipeline stages, saving intermediate images, & managing random state seeds

  Attributes
  ----------
  debug_dir : Optional[str]
      Destination directory for the debug images
  active : bool, default False
      Flag indicating whether image saving is enabled
  global_count : int, default 0
      Global incremental counter for tracking absolute order of images saved
  stage_count : Dict[str, int]
      Dict saving the internal increment count of images saved in each stage
  random : RandomState
      Isolated NumPy RandomState instance for deterministic pipeline steps
  """

  debug_dir: Optional[str] = None
  active: bool = False
  global_count: int = 0
  stage_count: dict[str, int] = {}
  random: RandomState = RandomState()

  @classmethod
  def set_directory(cls, debug_dir: Optional[str]) -> None:
    """
    Defines the output directory for debugging images & activates tracking

    Parameters
    ----------
    debug_dir : Optional[str]
        Path to directory where output images are stored
        If None, debugging is deactivated
    """
    cls.debug_dir = debug_dir

    if debug_dir is None:
      cls.active = False
    else:
      ensure_dir_exists(debug_dir)
      cls.active = True

  @classmethod
  def save_image(cls, stage: str, name: str, img: npt.NDArray[Any]) -> None:
    """
    Saves intermediate pipeline image if debugging is active.

    The generated filename scheme follows: `GG.stage.SS.name.png`
    Where GG is the global image count and SS is the stage-specific count.

    Parameters
    ----------
    stage : str
        Name of the current pipeline processing stage
    name : str
        Descriptive label for specific image state
    img : npt.NDArray[Any]
        Image matrix array to be save
    """
    if not cls.active:
      return

    count = cls.stage_count[stage] = cls.stage_count.get(stage, -1) + 1
    filename = f"{pad(cls.global_count)}.{stage}.{pad(count)}.{name}.png"

    # clean file path creation
    filepath = Path(cls.debug_dir) / filename
    imwrite(filepath, img)
    cls.global_count = cls.global_count + 1

  @classmethod
  def set_seed(cls, seed: Optional[int]):
    """
    Sets class-level seed for reproducible operations

    Parameters
    ----------
    seed : int
        Initialization seed passed to RandomState
    """
    cls.random.seed(seed)
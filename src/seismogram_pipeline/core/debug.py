from scipy import misc
from .dir import ensure_dir_exists
from numpy.random import RandomState
import imageio.v2 as imageio
import numpy.ma as ma
import numpy as np

def pad(number):
  numstr = str(number)
  return "0" + numstr if number < 10 else numstr

class Debug:

  debug_dir = None
  active = False
  global_count = 0
  stage_count = {}
  random = RandomState()

  @classmethod
  def set_directory(cls, debug_dir):
    cls.debug_dir = debug_dir

    if debug_dir is None:
      cls.active = False
    else:
      ensure_dir_exists(debug_dir)
      cls.active = True

  @classmethod
  def save_image(cls, stage, name, img):
    if not cls.active:
      return

    count = cls.stage_count[stage] = cls.stage_count.get(stage, -1) + 1
    filename = "%s.%s.%s.%s.png" % (pad(cls.global_count), stage, pad(count), name)
    if isinstance(img, ma.MaskedArray):
      img = img.filled(0) #convert masked array to regular array by replacing any masked value with 0

    if np.issubdtype(img.dtype, np.floating): #Convert float images to uin8 for PNG saving
      img = (img * 255).clip(0, 255).astype(np.uint8)
    elif not np.issubdtype(img.dtype, np.number):
      img = img.astype(np.uint8)

    imageio.imwrite(cls.debug_dir+"/"+filename, img)
    cls.global_count = cls.global_count + 1

  @classmethod
  def set_seed(cls, seed):
    cls.random.seed(seed)
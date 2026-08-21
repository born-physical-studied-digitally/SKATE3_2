# -*- coding: utf-8 -*-
"""
Binarization module for the seismogram pipeline.
"""

from .timer import timeStart, timeEnd

import numpy as np
import numpy.typing as npt
from typing import Any, Optional
from skimage import color
from scipy.signal import convolve2d
from skimage.morphology import remove_small_objects
from skimage.segmentation import watershed
from skimage.filters import sobel
from skimage.feature import canny
from .utilities import local_min
from .threshold import background_threshold
from .ridge_detection import find_ridges

def binary_image(
  image: npt.NDArray[Any],
  markers_trace: Optional[npt.NDArray[Any]] = None,
  markers_background: Optional[npt.NDArray[Any]] = None,
  min_trace_size: int = None,
  min_background_size: int = None,
) -> npt.NDArray[np.bool_]:
  """
  Creates a binary image from grayscale or color input image.
  Parameters
  ----------
  image : numpy array
      Can either be a color (3-D) or grayscale (2-D) image.
  markers_trace : Optional[npt.NDArray[Any]], optional
      Pre-determined seeds for the trace regions. If None, they are extracted
  markers_background : Optional[npt.NDArray[Any]] = None, optional
      Pre-determined seeds for the background regions. If None, they are extracted
  min_trace_size : int, default 6
      Minimum pixels to keep in foreground
  min_background_size : int, default 4
      Minimum pixels of background holes to keep inverted
  Returns
  -------
  image_bin : 2-D Boolean numpy array
      A 2-D array with the same shape as the input image. Foreground pixels
      are True, and background pixels are False.
  """
  
  if image.ndim != 2:
    image = color.rgb2gray(image)
  if markers_background is None:
    markers_background = get_background_markers(image)
  if markers_trace is None:
    markers_trace = get_trace_markers(image, markers_background)

  timeStart("watershed segmentation")
  image_bin = watershed_segmentation(image, markers_trace,
                     markers_background)
  timeEnd("watershed segmentation")
  #image_bin = image_bin & (~ fill_corners(canny(image)))

  timeStart("remove small segments and edges")
  image_bin = remove_small_segments_and_edges(image_bin, min_trace_size,
                        min_background_size)
  timeEnd("remove small segments and edges")
  return image_bin

def watershed_segmentation(
  image_gray: npt.NDArray[Any],
  markers_trace: npt.NDArray[Any],
  markers_background: npt.NDArray[Any],
  force_breaks: bool = True
) -> npt.NDArray[np.bool_]:
  """
  Segments the image into regions with one of two types (i.e. foreground
  and background) using a watershed algorithm.
  Parameters
  ----------
  image_gray : 2-D numpy array
      A grayscale image.
  markers_trace : 2-D Boolean numpy array
      An array with the same shape as image_gray, where the seeds of
      the trace regions are True.
  markers_background : 2-D Boolean numpy array
      An array with the same shape as image_gray, where the seeds of
      the background regions are True.
  force_breaks : bool, default True
      Placeholder flag to force segment breaks along detected Canny edges
  Returns
  -------
  image_bin : 2-D Boolean numpy array
      A 2-D array with the same shape as the input image. Foreground pixels
      are True, and background pixels are False.
  """

  # TODO: Add functionality for `force_breaks`
  # give option to exclude the canny edges from image_bin, to force breaks
  # along the edges and help with segmentation later on

  bin_markers = np.zeros_like(image_gray, dtype=int)
  bin_markers = np.where(markers_trace, 2, 0)
  bin_markers = np.where(markers_background, 1, bin_markers)

  image_sobel = sobel(image_gray)
  image_canny = canny(image_gray)
  edges = np.maximum(image_canny.astype(float), image_sobel)

  image_bin = watershed(edges, bin_markers)
  image_bin = image_bin == 2
  return image_bin

def get_background_markers(
  image_gray: npt.NDArray[Any], 
  prob_threshold: float = 0.95
) -> npt.NDArray[np.bool_]:
  """
  Finds the pixels that definitely belong in background regions.
  Parameters
  ----------
  image_gray : 2-D numpy array
      A grayscale image.
  Returns
  -------
  markers_background : 2-D Boolean numpy array
      An array with the same shape as image_gray, where the seeds of
      the background regions are True.
  """
  dark_pixels = image_gray <= background_threshold(image_gray, prob_threshold)

  minima = local_min(image_gray)
  markers_background = dark_pixels | minima
  return markers_background

def get_trace_markers(
  image_gray: npt.NDArray[Any],
  background: npt.NDArray[Any]
) -> npt.NDArray[np.bool_]:
  """
  Finds the pixels that definitely belong to traces.

  Parameters
  ----------
  image_gray : 2-D numpy array
      A grayscale image.
  background : 2-D numpy array of bools
      Pixels in the dark background.
  Returns
  -------
  markers_trace : 2-D Boolean numpy array
      An array with the same shape as image_gray, where the seeds of
      the trace regions are True.
  """
  ridges_h, ridges_v = find_ridges(image_gray, background)
  ridges_all = ridges_h | ridges_v
  return ridges_all

def remove_small_segments_and_edges(
  image_bin: npt.NDArray[np.bool_], 
  min_trace_size: int = 6, 
  min_edge_length: int = 4
) -> npt.NDArray[np.bool_]:
  """
  Removes small disconnected objects & artifacts from the foreground and background
  Parameters
  ----------
  image_bin : npt.NDArray[np.bool_]
      A binary 2-D image array. Modified in place during operations
  min_trace_size : int, default 6
      Maximum size of small foreground objects to be removed
  min_edge_length : int, default 4
      Maximum size of small background holes to be filled
  Returns
  -------
  image_bin : 2-D Boolean numpy array
      Cleaned version of original input array
  """
  remove_small_objects(image_bin, min_size = min_trace_size, connectivity=2,
             in_place = True)
  image_bin = ~image_bin
  remove_small_objects(image_bin, min_size = min_edge_length, connectivity=2,
             in_place = True)
  image_bin = ~image_bin
  return image_bin


def fill_corners(image_bin: npt.NDArray[Any]) -> npt.NDArray[np.bool_]:
  """
  Identifies and fills the single-pixel diagonal step-corners using custom 2-D kernels.
  
  Parameters
  ----------
  image_bin : npt.NDArray[Any]
      Binary 2-D image array
  
  Returns
  -------
  filled_image : npt.NDArray[np.bool_]
      Binary 2-D array with structural diagonal step corners filled in    
  """
  arr = np.where(image_bin, 1, -1)

  ul_kernel = np.array([[-1, 1, 0], [1, 0, 0], [0, 0, 0]])
  ur_kernel = np.array([[0, 1, -1], [0, 0, 1], [0, 0, 0]])
  ll_kernel = np.array([[0, 0, 0], [1, 0, 0], [-1, 1, 0]])
  lr_kernel = np.array([[0, 0, 0], [0, 0, 1], [0, 1, -1]])

  upper_left = convolve2d(arr, ul_kernel, mode = 'same', boundary = 'symm')
  upper_right = convolve2d(arr, ur_kernel, mode = 'same', boundary = 'symm')
  lower_left = convolve2d(arr, ll_kernel, mode = 'same', boundary = 'symm')
  lower_right = convolve2d(arr, lr_kernel, mode = 'same', boundary = 'symm')
  corners = ((upper_left == 3) | (upper_right == 3) | (lower_left == 3) |
        (lower_right == 3))
  return image_bin | corners


def peak_local_max_rows(
  a: npt.NDArray[Any],
  include_border: bool = False
) -> npt.NDArray[np.bool_]:
  """
  Finds row-wise local maxima along the columns in a 2-D array
  Parameters
  ----------
  a : npt.NDArray[Any]
      A 2-D numeric input array
  include_border : bool, default False
      Flag for whether to include border points as potential local maxima
  Returns
  -------
  maxima : npt.NDArray[np.bool_]
      Boolean mask of row-wise peak local maxima locations
  """
  maxima = np.zeros_like(a,dtype=bool)
  maxima = np.logical_and( \
            np.hstack((np.ones((a.shape[0],1)) * include_border,
                a[:,1:] >= a[:,:-1])), \
            np.hstack((a[:,:-1] >= a[:,1:],
                np.ones((a.shape[0],1)) * include_border)))
  return maxima

def peak_local_max_cols(
  a: npt.NDArray[Any],
  include_border: bool = False
) -> npt.NDArray[np.bool_]:
  """
  Finds column-wise local maxima along the rows in a 2-D array
  Parameters
  ----------
  a : npt.NDArray[Any]
      A 2-D numeric input array
  include_border : bool, default False
      Flag for whether to include border points as potential local maxima
  Returns
  -------
  maxima : npt.NDArray[np.bool_]
      Boolean mask of column-wise peak local maxima locations
  """
  maxima = np.zeros_like(a,dtype=bool)
  maxima = np.logical_and( \
            np.vstack((np.ones((1,a.shape[1])) * include_border,
                a[1:,:] >= a[:-1,:])), \
            np.vstack((a[:-1,:] >= a[1:,:],
                np.ones((1,a.shape[1])) * include_border)))
  return maxima

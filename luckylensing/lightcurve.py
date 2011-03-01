# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from __future__ import division
from math import sqrt
import numpy
import utils
import magpat as magpat_mod

class SourceProfile(numpy.ndarray):
    arg_name = "source_profile"

class SourceFFT(numpy.ndarray):
    arg_name = "source_fft"

def _flat(r2, source_radius2, width, height):
    width2 = width*width
    height2 = height*height
    if source_radius2 <= 0.25*width2 + 0.25*height2:
        return r2 <= source_radius2
    source_radius = sqrt(source_radius2)
    m = 1.0/((width+height)*source_radius)
    b = (source_radius2 +
         0.5*(width+height)*source_radius +
         0.25*width*height)
    return numpy.clip(-m*r2 + m*b, 0.0, 1.0)

def _gaussian(r2, source_radius2, width, height):
    return numpy.exp(-r2 / (2.0*source_radius2))

all_profile_types = {"flat": _flat, "gaussian": _gaussian}

def source_profile(magpat, source_radius, profile_type="flat"):
    """Create a source profile suitable to convolve the magpat with.

    This function returns a pair of two-dimensional NumPy arrays.  The
    first is the source profile itself, the second is its Fourier
    transform.

    Parameters:

        magpat           the magnification pattern which the source
                         profile shall be suited for
        source_radius    radius or standard deviation of the source
        profile_type     currently supports "flat" and "gaussian"
    """
    source_radius2 = source_radius * source_radius
    ypixels, xpixels = magpat.shape
    width = magpat.region.width / xpixels
    width2 = width * width
    height = magpat.region.height / ypixels
    height2 = height * height
    kernel = numpy.indices((ypixels // 2 + 1, xpixels // 2 + 1))
    kernel *= kernel
    kernel = height2 * kernel[0] + width2 * kernel[1]
    try:
        profile = all_profile_types[profile_type.strip().lower()]
    except KeyError:
        raise ValueError("Unknown source profile type: " + profile_type)
    kernel = profile(kernel, source_radius2, width, height)
    kernel = numpy.vstack((kernel[:-1], numpy.flipud(kernel[1:])))
    kernel = numpy.hstack((kernel[:,:-1], numpy.fliplr(kernel[:,1:])))
    kernel = kernel / float(numpy.sum(kernel))
    kernel_fft = numpy.fft.rfft2(kernel)
    return kernel.view(SourceProfile), kernel_fft.view(SourceFFT)

def convolve(magpat, source_fft, convolved_pattern=None):
    """Returns the convolution of a magnification pattern with a source profile.

    Parameters:

        magpat           the magnification pattern
        source_fft       the Fourier transform of the source profile as
                         returned by the source_profile() function
        convolved_pattern
                         output array; may conincide with magpat to
                         convolve in place
    """
    shape = magpat.shape
    xcorrect = ycorrect = None
    if shape[0] & 1:
        utils.logger.info("Correcting for an odd pixel height of the pattern")
        ycorrect = -1
    if shape[1] & 1:
        utils.logger.info("Correcting for an odd pixel width of the pattern")
        xcorrect = -1
    if convolved_pattern is None:
        convolved_pattern = magpat_mod.Magpat.empty_like(magpat)
    convolved_pattern[:ycorrect, :xcorrect] = numpy.fft.irfft2(
        numpy.fft.rfft2(magpat[:ycorrect, :xcorrect]) * source_fft)
    if shape[0] & 1:
        convolved_pattern[-1] = convolved_pattern[-2]
    if shape[1] & 1:
        convolved_pattern[:,-1] = convolved_pattern[:,-2]
    return convolved_pattern

class LightCurve(numpy.ndarray):
    """One-dimensional NumPy array representing a light curve.
    """

    arg_name = "light_curve"

    def __new__(cls, samples, buffer=None, offset=0):
        return numpy.ndarray.__new__(
            cls, samples, numpy.float32, buffer, offset)

def light_curve(magpat, curve_x0, curve_y0, curve_x1, curve_y1,
                curve_samples=256):
    """Extract a light curve from a magnification pattern.

    Returns a LightCurve instance.

    Parameters:

        magpat           the magnification pattern
        curve_x0, curve_y0, curve_x1, curve_y1
                         start and end point coordinates of the light
                         curve in source plane coordinates
        curve_samples    number of samples
    """
    curve = LightCurve(curve_samples)
    magpat.params.light_curve(
        magpat, curve, curve_x0, curve_y0, curve_x1, curve_y1)
    return curve

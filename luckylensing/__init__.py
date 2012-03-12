# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

"""Lucky Lensing Library

This is the main Python package of the Lucky Lensing Library.

WWW address: http://github.com/smarnach/luckylensing

Classes:

LensConfig        -- a configuration of lenses in the lens plane
LightCurve        -- a light curve
Magpat            -- a magnification pattern
Rayshooter        -- a class controlling a multi-threaded ray shooting run

Functions:

binary_lenses     -- return a binary lens configuration
convolve          -- convolve a magnification pattern with a source profile
globular_cluster  -- return a globular cluster lens configuration
light_curve       -- extract a light curve from a magnification pattern
polygonal_lenses  -- return lenses arranged as a regular polygon
rayshoot          -- generate a magnification pattern by ray shooting
read_fits         -- read a magnification pattern from a FITS file
rectangle         -- return a paraxial rectangle instance
source_profile    -- create a new source profile
write_fits        -- write a magnification pattern to a FITS file

Other:

all_profile_types -- a dictionary of registered source profile types
libll             -- a subpackage wrapping the C kernel of this library
logger            -- the logging.Logger instance used by the library
stdout_handler    -- the default logging handler

Example usage:

>>> import luckylensing as ll
>>> lenses = ll.binary_lenses(1.2, 5e-4)
>>> region = ll.rectangle(0.35, 0.0, radius=0.15)
>>> magpat = ll.rayshoot(lenses, region)
>>> magpat.convolve(source_radius=0.005, profile_type="flat")
>>> magpat.write_fits("magpat.fits")
>>> lc = ll.light_curve(magpat, 0.25, -0.05, 0.45, 0.1)
>>> lc.tofile("lightcurve.txt", sep="\\n")

The above code will create a FITS file 'magpat.fits' containing a
magnification pattern convolved with a flat source profile and a text
file 'lightcurve.txt' with samples of a light curve extracted from
this pattern.
"""

from .utils import logger, stdout_handler, rectangle
from .lensconfig import (
    LensConfig, binary_lenses, globular_cluster, polygonal_lenses)
from .magpat import Magpat, Rayshooter, rayshoot
from .lightcurve import (
    all_profile_types, source_profile, convolve, LightCurve, light_curve)
try:
    from .fits import write_fits, read_fits
    del fits
except ImportError:
    pass

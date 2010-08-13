"""Wrap the C functions in the ll library with an Pythonic interface.

The functions in the ll ("Lucky Lensing") library allow for high
performance computations in the context of gravitational lensing.
This module provides Python bindings for the functions and data types
in this C library.

Classes:

Lens              -- coordinates and mass of a point lens
Lenses            -- array of point lenses
Rect              -- coordinates of a rectangle
Patches           -- subpatch pattern for hierarchical ray shooting
MagPatternParams  -- parameters of a magnification pattern
Progress          -- helper for some methods of Rayshooter
Rayshooter        -- compute magnification patterns

Functions:

render_magpattern_greyscale
                  -- render a magnification pattern
"""

import ctypes as _c
import numpy as _np
from numpy.ctypeslib import ndpointer as _ndpointer

# Import symbols from libll.so to the module namespace
_libll = _c.CDLL("./libll.so")
_shoot_single_ray = _libll.ll_shoot_single_ray
_rayshoot_rect = _libll.ll_rayshoot_rect
_get_subpatches = _libll.ll_get_subpatches
_rayshoot_subpatches = _libll.ll_rayshoot_subpatches
_finalise_subpatches = _libll.ll_finalise_subpatches
_rayshoot = _libll.ll_rayshoot
_ray_hit_pattern = _libll.ll_ray_hit_pattern
_source_images = _libll.ll_source_images
_render_magpattern_greyscale = _libll.ll_render_magpattern_greyscale
_light_curve = _libll.ll_light_curve

class Lens(_c.Structure):

    """Store the position and mass of a point lens in a C struct.

    x    -- x-coordinate in lens plane coordinates
    y    -- y-coordinate in lens plane coordinates
    mass -- Einstein radius of the lens squared (this is proportional
            to the lens' mass)
    """

    _fields_ = [("x", _c.c_double),
                ("y", _c.c_double),
                ("mass", _c.c_double)]

    def __repr__(self):
        return "%s.%s(%0.5g, %0.5g, %0.5g)" % (
            self.__class__.__module__, self.__class__.__name__,
            self.x, self.y, self.mass)

class Lenses(_c.Structure):

    """Store an C array of Lens objects.

    num_lenses -- number of Lens objects in the array
    lens       -- the actual C array
    """

    _fields_ = [("num_lenses", _c.c_uint),
                ("lens", _c.POINTER(Lens))]

    def __init__(self, lens_list):
        """Initialise the C array from a Python sequence of sequences.

        Each element of the sequence lens_list shall be a sequence of
        three floats, containing the coordinates and mass of the
        respective lens.  For example

        Lenses([(0,0,1), (1.2, 0, .0004)])

        will create an array of the two given lenses
        """
        l = len(lens_list)
        super(Lenses, self).__init__(l, (Lens*l)(*map(tuple, lens_list)))

class Rect(_c.Structure):

    """Store the coordinates of a rectangle in a C struct.

    The rectangle must be aligned with the coordinate system.

    x      -- the x-coordinate of the left boundary
    y      -- the y-coordinate of the lower boundary
    width  -- the distance between left and right boundary
    height -- the distance between upper and lower boundary
    """

    _fields_ = [("x", _c.c_double),
                ("y", _c.c_double),
                ("width", _c.c_double),
                ("height", _c.c_double)]

    def __repr__(self):
        return "%s.%s(%0.5g, %0.5g, %0.5g, %0.5g)" % (
            self.__class__.__module__, self.__class__.__name__,
            self.x, self.y, self.width, self.height)

    def __setattr__(self, name, value):
        # This method is needed for the consistency magic in the
        # MagPatternParams and Patches classes
        super(Rect, self).__setattr__(name, value)
        if getattr(self, "callback", None) and name in ("width", "height"):
            self.callback()

class Patches(_c.Structure):

    """Stores the pattern of subpatches for hierarchic ray shooting.
    """

    _fields_ = [("rect", Rect),
                ("xrays", _c.c_int),
                ("yrays", _c.c_int),
                ("width_per_xrays", _c.c_double),
                ("height_per_yrays", _c.c_double),
                ("hit", _c.POINTER(_c.c_char)),
                ("num_patches", _c.c_uint)]

    def __init__(self, rect, hit):
        yrays, xrays = hit.shape
        super(Patches, self).__init__(rect, xrays, yrays,
            hit=hit.ctypes.data_as(_c.POINTER(_c.c_char)), num_patches = 0)

    # The following methods try to always keep the quotients
    # width_per_xrays and height_per_yrays consistent.  These ratios
    # cache redundant information (see the _update_ratios method).

    def __setattr__(self, name, value):
        # Update ratios if needed; disallow direct write access
        if name in ("width_per_xrays", "height_per_yrays"):
            raise AttributeError, "Attribute %s is not writable" % name
        super(Patches, self).__setattr__(name, value)
        if name in ("rect", "xrays", "yrays"):
            self._update_ratios()

    def __getattribute__(self, name):
        # If the rect attribute is read, ctypes returns a new Rect
        # object, which is nonetheless linked to the data in the
        # Patches class.  So we have to add a callback to the new
        # object to ensure consistency.
        value = super(Patches, self).__getattribute__(name)
        if name == "rect":
            value.callback = (super(Patches, self).
                              __getattribute__("_update_ratios"))
        return value

    def _update_ratios(self):
        try:
            super(Patches, self).__setattr__(
                "width_per_xrays", self.rect.width/self.xrays)
            super(Patches, self).__setattr__(
                "height_per_yrays", self.rect.height/self.yrays)
        except ZeroDivisionError:
            pass

class MagPatternParams(_c.Structure):
    _fields_ = [("lenses", Lenses),
                ("region", Rect),
                ("xpixels", _c.c_uint),
                ("ypixels", _c.c_uint),
                ("pixels_per_width", _c.c_double),
                ("pixels_per_height", _c.c_double)]

    def __init__(self, lenses=[], region=(-1.,-1.,2.,2.),
                 xpixels=1024, ypixels=1024):
        super(MagPatternParams, self).__init__(Lenses(lenses), region,
                                               xpixels, ypixels)

    def __setattr__(self, name, value):
        if name in ("pixels_per_width", "pixels_per_height"):
            raise AttributeError, "Attribute %s is not writable" % name
        super(MagPatternParams, self).__setattr__(name, value)
        if name in ("region", "xpixels", "ypixels"):
            self._update_ratios()

    def __getattribute__(self, name):
        value = super(MagPatternParams, self).__getattribute__(name)
        if name == "region":
            value.callback = (super(MagPatternParams, self).
                              __getattribute__("_update_ratios"))
        return value

    def _update_ratios(self):
        try:
            super(MagPatternParams, self).__setattr__(
                "pixels_per_width", self.xpixels / self.region.width)
            super(MagPatternParams, self).__setattr__(
                "pixels_per_height", self.ypixels / self.region.height)
        except ZeroDivisionError:
            pass

    def shoot_single_ray(self, x, y):
        mag_x = _c.c_double()
        mag_y = _c.c_double()
        b = bool(_shoot_single_ray(self, x, y, mag_x, mag_y))
        return mag_x.value, mag_y.value, b

    def rayshoot_rect(self, magpat, rect, xrays, yrays):
        _rayshoot_rect(self, magpat, rect, xrays, yrays)

    def ray_hit_pattern(self, buf, rect):
        _ray_hit_pattern(self, buf, rect)

    def source_images(self, buf, rect, xrays, yarays, refine,
                      source_x, source_y, source_r):
        _source_images(self, buf, rect, xrays, yarays, refine,
                      source_x, source_y, source_r)

    def light_curve(self, magpat, curve, num_points, x0, y0, x1, y1):
        _light_curve(self, magpat, curve, num_points, x0, y0, x1, y1)

Progress = _c.c_double
"""Type for the Progress argument of some methods of Rayshooter.

The current value can be extracted by reading the value attribute.
"""
# It should not be necessary for user code to use anything from the
# ctypes module, so we expose this type

# Constants to select a ra shooting kernel.  These are enum constants in C.
KERNEL_SIMPLE = 0
KERNEL_BILINEAR = 1
KERNEL_TRIANGULATED = 2

class Rayshooter(_c.Structure):
    _fields_ = [("params", _c.POINTER(MagPatternParams)),
                ("kernel", _c.c_int),
                ("levels", _c.c_uint),
                ("refine", _c.c_int),
                ("refine_final", _c.c_int),
                ("cancel_flag", _c.c_int)]

    def __init__(self, params, levels):
        if type(params) is not MagPatternParams:
            params = MagPatternParams(*params)
        super(Rayshooter, self).__init__(_c.pointer(params), KERNEL_BILINEAR,
                                         levels, 15, 25, False)

    def cancel(self):
        self.cancel_flag = True

    def get_subpatches(self, patches):
        _get_subpatches(self.params, patches)

    def start_subpatches(self, magpat, patches, progress=Progress()):
        self.cancel_flag = False
        _rayshoot_subpatches(self, magpat, patches, self.levels - 1, progress)

    def finalise_subpatches(self, magpat, patches):
        _finalise_subpatches(self, magpat, patches)

    def start(self, magpat, rect, xrays, yrays, progress=Progress()):
        self.cancel_flag = False
        _rayshoot(self, magpat, rect, xrays, yrays, progress)

# ctypes prototypes for the functions in libll.so
_shoot_single_ray.argtypes = [_c.POINTER(MagPatternParams),
                              _c.c_double,
                              _c.c_double,
                              _c.POINTER(_c.c_double),
                              _c.POINTER(_c.c_double)]
_shoot_single_ray.restype = _c.c_int

_rayshoot_rect.argtypes = [_c.POINTER(MagPatternParams),
                           _ndpointer(_np.int, flags="C_CONTIGUOUS"),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int]
_rayshoot_rect.restype = None

_get_subpatches.argtypes = [_c.POINTER(MagPatternParams),
                            _c.POINTER(Patches)]
_get_subpatches.restype = None

_rayshoot_subpatches.argtypes = [_c.POINTER(Rayshooter),
                                 _ndpointer(flags="C_CONTIGUOUS"),
                                 _c.POINTER(Patches),
                                 _c.c_uint,
                                 _c.POINTER(_c.c_double)]
_rayshoot_subpatches.restype = None

_finalise_subpatches.argtypes = [_c.POINTER(Rayshooter),
                                 _ndpointer(flags="C_CONTIGUOUS"),
                                 _c.POINTER(Patches)]
_finalise_subpatches.restype = None

_rayshoot.argtypes = [_c.POINTER(Rayshooter),
                      _ndpointer(flags="C_CONTIGUOUS"),
                      _c.POINTER(Rect),
                      _c.c_int,
                      _c.c_int,
                      _c.POINTER(_c.c_double)]
_rayshoot.restype = None

_ray_hit_pattern.argtypes = [_c.POINTER(MagPatternParams),
                             _ndpointer(_np.uint8, flags="C_CONTIGUOUS"),
                             _c.POINTER(Rect)]
_ray_hit_pattern.restype = None

_source_images.argtypes = [_c.POINTER(MagPatternParams),
                           _ndpointer(_np.uint8, flags="C_CONTIGUOUS"),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int,
                           _c.c_int,
                           _c.c_double,
                           _c.c_double,
                           _c.c_double]
_source_images.restype = None

_render_magpattern_greyscale.argtypes = [_ndpointer(_np.uint8, flags="C_CONTIGUOUS"),
                                         _ndpointer(_np.float32, flags="C_CONTIGUOUS"),
                                         _c.c_uint]
_render_magpattern_greyscale.restype = None

def render_magpattern_greyscale(buf, magpat):
    """Render the magnification pattern using a logarithmic greyscale palette.

    buf    -- a contiguous C array of char which the image will be
              rendered into
    magpat -- a contiguous C array of int with the magpattern counts

    Both parameters are assumed to be numpy array of the same size
    (meaning there size attributes coincide).  They do not need to
    have the same shape.
    """
    assert buf.size == magpat.size
    _render_magpattern_greyscale(buf, magpat, magpat.size)

_light_curve.argtypes = [_c.POINTER(MagPatternParams),
                         _ndpointer(_np.float32, flags="C_CONTIGUOUS"),
                         _ndpointer(_np.double, flags="C_CONTIGUOUS"),
                         _c.c_uint,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double]
_light_curve.restype = None

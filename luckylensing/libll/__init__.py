# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

"""Wrap the C functions in the ll library with an Pythonic interface.

The functions in the Lucky Lensing Library (libll.so) allow for high
performance computations in the context of gravitational lensing.
This module provides Python bindings for the functions and data types
in this C library.

Classes:

Lens              -- coordinates and mass of a point lens
Lenses            -- array of point lenses
Rect              -- coordinates of a rectangle
Patches           -- subpatch pattern for hierarchical ray shooting
MagpatParams      -- parameters of a magnification pattern
Progress          -- helper for some methods of BasicRayshooter
BasicRayshooter   -- compute magnification patterns

Functions:

render_magpat_greyscale
                  -- render a magnification pattern using grey shades
render_magpat_palette
                  -- render a magnification pattern using a color palette
"""

import os.path as _path
import ctypes as _c
import numpy as _np
from numpy.ctypeslib import ndpointer as _ndpointer

# Import symbols from libll.so to the module namespace
_libll = _c.CDLL(_path.join(_path.dirname(__file__) or  ".", "libll.so"))
_shoot_single_ray = _libll.ll_shoot_single_ray
_rayshoot_rect = _libll.ll_rayshoot_rect
_get_subpatches = _libll.ll_get_subpatches
_rayshoot_subpatches = _libll.ll_rayshoot_subpatches
_finalise_subpatches = _libll.ll_finalise_subpatches
_rayshoot = _libll.ll_rayshoot
_ray_hit_pattern = _libll.ll_ray_hit_pattern
_source_images = _libll.ll_source_images
_render_magpat_greyscale = _libll.ll_render_magpat_greyscale
_render_magpat_gradient = _libll.ll_render_magpat_gradient
_light_curve = _libll.ll_light_curve
del _libll

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
        """Initialise the C array from lens_list.

        The parameter might be another Lenses instance, a NumPy array
        or a Python sequence of sequences.

        If lens_list is a NumPy array, it must be C contiguuous.  Keep
        a reference to the data to make sure it is not garbage
        collected.

        If lens_list is a Python sequence, each element shall be a
        sequence of three floats, containing the coordinates and mass
        of the respective lens.  For example

        Lenses([(0., 0., 1.), (1.2, 0., .0004)])

        will create an array of the two given lenses.
        """
        if isinstance(lens_list, Lenses):
            _c.Structure.__init__(self, lens_list.num_lenses, lens_list.lens)
        elif isinstance(lens_list, _np.ndarray):
            _c.Structure.__init__(self, len(lens_list),
                                  lens_list.ctypes.data_as(_c.POINTER(Lens)))
        else:
            l = len(lens_list)
            _c.Structure.__init__(self, l, (Lens*l)(*map(tuple, lens_list)))

class Rect(_c.Structure):

    """Store the coordinates of a rectangle in a C struct.

    The rectangle must be aligned with the coordinate system.

    x      -- the x-coordinate of the left boundary
    y      -- the y-coordinate of the lower boundary
    width  -- the distance between left and right boundary
    height -- the distance between upper and lower boundary

    For convenience, the following read-only properties are provided:

    x0     -- same as x
    y0     -- same as y
    x1     -- same as x + width
    y1     -- same as y + height
    """

    _fields_ = [("x", _c.c_double),
                ("y", _c.c_double),
                ("width", _c.c_double),
                ("height", _c.c_double)]

    def __repr__(self):
        return "%s.%s(%0.5g, %0.5g, %0.5g, %0.5g)" % (
            self.__class__.__module__, self.__class__.__name__,
            self.x, self.y, self.width, self.height)

    def __str__(self):
        return "x=%0.3g, y=%0.3g, width=%0.3g, height=%0.3g" % (
            self.x, self.y, self.width, self.height)

    def __setattr__(self, name, value):
        # This method is needed for the consistency magic in the
        # MagpatParams and Patches classes
        super(Rect, self).__setattr__(name, value)
        if getattr(self, "callback", None) and name in ("width", "height"):
            self.callback()

    def __iter__(self):
        """Iterator for easy conversion to a tuple.
        """
        yield self.x
        yield self.y
        yield self.width
        yield self.height

    @property
    def x0(self):
        return self.x

    @property
    def y0(self):
        return self.y

    @property
    def x1(self):
        return self.x + self.width

    @property
    def y1(self):
        return self.y + self.height

class Patches(_c.Structure):

    """Stores the pattern of subpatches for hierarchic ray shooting.
    """

    _fields_ = [("rect", Rect),
                ("xrays", _c.c_int),
                ("yrays", _c.c_int),
                ("level", _c.c_uint),
                ("width_per_xrays", _c.c_double),
                ("height_per_yrays", _c.c_double),
                ("hit", _c.POINTER(_c.c_uint8)),
                ("num_patches", _c.c_uint)]

    def __init__(self, rect, level, xrays=None, yrays=None, hit=None):
        """Create a patches object with the given rect and subpatch pattern."""
        if hit is not None:
            yrays, xrays = hit.shape
        else:
            hit = _np.empty((yrays, xrays), _c.c_uint8)
        self.hit_array = hit
        _c.Structure.__init__(self, rect, xrays, yrays, level,
            hit=hit.ctypes.data_as(_c.POINTER(_c.c_uint8)), num_patches=0)

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

class MagpatParams(_c.Structure):

    """Parameters describing a magnification pattern.

    This structure contains all information needed to describe a
    magnification pattern, but does not include the parameters of the
    actual shooting process.  In particular they are

    lenses            -- list of lenses in the lens plane
    region            -- coordinates of the pattern in the source plane
    xpixels           -- x resolution of the pattern
    ypixels           -- y resolution of the pattern
    pixels_per_width  -- xpixels/region.width; needed internally and kept
                         up to date autommatically
    pixels_per_hieght -- ypixels/region.height; needed internally and kept
                         up to date autommatically
    """

    _fields_ = [("lenses", Lenses),
                ("region", Rect),
                ("xpixels", _c.c_uint),
                ("ypixels", _c.c_uint),
                ("pixels_per_width", _c.c_double),
                ("pixels_per_height", _c.c_double)]

    def __init__(self, lenses, region, xpixels, ypixels):
        _c.Structure.__init__(self, Lenses(lenses), region, xpixels, ypixels)

    # The following methods try to always keep the quotients
    # pixels_per_width and pixels_per_height consistens.  The same
    # pattern is used in the Patches class above.

    def __setattr__(self, name, value):
        if name in ("pixels_per_width", "pixels_per_height"):
            raise AttributeError, "Attribute %s is not writable" % name
        super(MagpatParams, self).__setattr__(name, value)
        if name in ("region", "xpixels", "ypixels"):
            self._update_ratios()

    def __getattribute__(self, name):
        value = super(MagpatParams, self).__getattribute__(name)
        if name == "region":
            value.callback = (super(MagpatParams, self).
                              __getattribute__("_update_ratios"))
        return value

    def _update_ratios(self):
        try:
            super(MagpatParams, self).__setattr__(
                "pixels_per_width", self.xpixels / self.region.width)
            super(MagpatParams, self).__setattr__(
                "pixels_per_height", self.ypixels / self.region.height)
        except ZeroDivisionError:
            pass

    def shoot_single_ray(self, x, y):
        """Return the magnification pattern coordinates of a single ray.

        The arguments x and y give the lens plane coordinates of the
        ray to shoot.  The return value is a tuple of length 3.  The
        first two components of give the coordinates where the ray
        hits the source plane after being deflected by the lenses.
        The coordinates are pixel coordinates in the magnification
        pattern, but given as floating point numbers.  The third
        component is a bool describing if the magnification pattern
        region.
        """
        mag_x = _c.c_double()
        mag_y = _c.c_double()
        b = _shoot_single_ray(self, x, y, mag_x, mag_y) == 0x0F
        return mag_x.value, mag_y.value, b

    def rayshoot_rect(self, magpat, rect, xrays, yrays):
        _rayshoot_rect(self, magpat, rect, xrays, yrays)

    def ray_hit_pattern(self, buf, rect):
        _ray_hit_pattern(self, buf, rect)

    def source_images(self, buf, rect, xrays, yarays, refine,
                      source_x, source_y, source_r):
        _source_images(self, buf, rect, xrays, yarays, refine,
                      source_x, source_y, source_r)

    def light_curve(self, magpat, curve, x0, y0, x1, y1):
        _light_curve(self, magpat, curve, curve.size, x0, y0, x1, y1)

Progress = _c.c_double
"""Type for the progress argument of some methods of BasicRayshooter.

The current value can be extracted by reading the attribute 'value'.
"""
# It should not be necessary for user code to use anything from the
# ctypes module, so we expose this type

# Constants to select a ray shooting kernel.  These are enum constants in C.
all_kernels = {"simple": 0, "bilinear": 1, "triangulated": 2}

class BasicRayshooter(_c.Structure):

    """A class controlling the ray shooting process.
    """

    _fields_ = [("params", _c.POINTER(MagpatParams)),
                ("kernel", _c.c_int),
                ("refine", _c.c_int),
                ("refine_kernel", _c.c_int),
                ("cancel_flag", _c.c_int)]

    def __init__(self, params, kernel, refine, refine_kernel):
        if kernel not in all_kernels.values():
            try:
                kernel = all_kernels[kernel.strip().lower()]
            except KeyError:
                raise ValueError("Unknown ray shooting kernel '%s'" % kernel)
        _c.Structure.__init__(self, _c.pointer(params), kernel,
                              refine, refine_kernel, False)

    def cancel(self):
        """Cancel the currently running ray shooting function.

        Only useful in multithreaded applications.
        """
        self.cancel_flag = True

    def get_subpatches(self, patches):
        _get_subpatches(self.params, patches)

    def run_subpatches(self, magpat, patches, progress=Progress()):
        _rayshoot_subpatches(self, magpat, patches, progress)

    def finalise_subpatches(self, magpat, patches):
        if isinstance(magpat, list):
            if self.kernel != all_kernels["triangulated"]:
                for i, m in enumerate(magpat):
                    magpat[i] = m.view(_np.int32)
            for m in magpat[1:]:
                magpat[0] += m
            magpat = magpat[0]
        _finalise_subpatches(self, magpat, patches)

    def run(self, magpat, rect, xrays, yrays, levels, progress=Progress()):
        """Start the actual ray shooting.
        """
        self.cancel_flag = False
        _rayshoot(self, magpat, rect, xrays, yrays, levels, progress)

# ctypes prototypes for the functions in libll.so
_shoot_single_ray.argtypes = [_c.POINTER(MagpatParams),
                              _c.c_double,
                              _c.c_double,
                              _c.POINTER(_c.c_double),
                              _c.POINTER(_c.c_double)]
_shoot_single_ray.restype = _c.c_int

_rayshoot_rect.argtypes = [_c.POINTER(MagpatParams),
                           _ndpointer(_c.c_uint32, flags="C_CONTIGUOUS"),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int]
_rayshoot_rect.restype = None

_get_subpatches.argtypes = [_c.POINTER(MagpatParams),
                            _c.POINTER(Patches)]
_get_subpatches.restype = None

_rayshoot_subpatches.argtypes = [_c.POINTER(BasicRayshooter),
                                 _ndpointer(flags="C_CONTIGUOUS"),
                                 _c.POINTER(Patches),
                                 _c.POINTER(_c.c_double)]
_rayshoot_subpatches.restype = None

_finalise_subpatches.argtypes = [_c.POINTER(BasicRayshooter),
                                 _ndpointer(flags="C_CONTIGUOUS"),
                                 _c.POINTER(Patches)]
_finalise_subpatches.restype = None

_rayshoot.argtypes = [_c.POINTER(BasicRayshooter),
                      _ndpointer(flags="C_CONTIGUOUS"),
                      _c.POINTER(Rect),
                      _c.c_int,
                      _c.c_int,
                      _c.c_uint,
                      _c.POINTER(_c.c_double)]
_rayshoot.restype = None

_ray_hit_pattern.argtypes = [_c.POINTER(MagpatParams),
                             _ndpointer(_c.c_uint8, flags="C_CONTIGUOUS"),
                             _c.POINTER(Rect)]
_ray_hit_pattern.restype = None

_source_images.argtypes = [_c.POINTER(MagpatParams),
                           _ndpointer(_c.c_uint8, flags="C_CONTIGUOUS"),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int,
                           _c.c_int,
                           _c.c_double,
                           _c.c_double,
                           _c.c_double]
_source_images.restype = None

_render_magpat_greyscale.argtypes = [_ndpointer(_c.c_float, flags="C_CONTIGUOUS"),
                                     _ndpointer(_c.c_uint8, flags="C_CONTIGUOUS"),
                                     _c.c_uint,
                                     _c.c_uint,
                                     _c.c_float,
                                     _c.c_float]
_render_magpat_greyscale.restype = None

def render_magpat_greyscale(magpat, min_mag=None, max_mag=None, buf=None):
    """Render the magnification pattern using a logarithmic greyscale gradient.

    magpat  -- a contiguous C array of float with the magpat counts
    min_mag,
    max_mag -- The magnifications corresponding to black and white,
               respectively.  If either of these parameters is None, the
               minimum and maximum values in the pattern are used.
    buf     -- a contiguous C array of uint8_t which the image will be
               rendered into; if None is given, the function will allocate
               a suitable buffer

    Both parameters are assumed to be numpy arrays of the same size
    (meaning there size attributes coincide).  They do not need to
    have the same shape.

    The function returns the buffer with the greyscale data.  If you
    provided this buffer, the return value can be ignored.
    """
    if buf is None:
        buf = _np.empty(magpat.shape, _c.c_uint8)
    else:
        assert buf.size == magpat.size
    if min_mag is None:
        min_mag = -1.0
    if max_mag is None:
        max_mag = -1.0
    _render_magpat_greyscale(magpat, buf, magpat.shape[1], magpat.shape[0],
                             min_mag, max_mag)
    return buf

_render_magpat_gradient.argtypes = [_ndpointer(_c.c_float, flags="C_CONTIGUOUS"),
                                    _ndpointer(_c.c_uint8, flags="C_CONTIGUOUS"),
                                    _c.c_uint,
                                    _c.c_uint,
                                    _c.c_float,
                                    _c.c_float,
                                    _ndpointer(_c.c_uint8, flags="C_CONTIGUOUS"),
                                    _ndpointer(_c.c_uint, flags="C_CONTIGUOUS")]
_render_magpat_gradient.restype = None

def render_magpat_gradient(magpat, colors=None, steps=None, min_mag=None,
                           max_mag=None, buf=None):
    """Render the magnification pattern logarithmically with the given gradient.

    magpat  -- a contiguous C array of float with the magpat counts
    colors  -- a sequence of RGB triples describing colors in the gradient
    steps   -- the number of steps to use between the color with the same
               index and the next one.  The length of this needs to be one
               less than the number of colors.  If colors and steps are
               omitted, a standard palette is used.
    min_mag,
    max_mag -- The magnifications corresponding to the ends of the
               gradient.  If either of these parameters is None, the
               minimum and maximum values in the pattern are used.
    buf     -- a contiguous C array of uint8_t which the image will be
               rendered into; if None is given, the function will allocate
               a suitable buffer

    The function returns the buffer with the image data.  If you
    provided this buffer, the return value can be ignored.
    """
    if colors is None:
        colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
                  (195, 16, 16), (249, 249, 70), (255, 255, 255)]
    if steps is None:
        steps = [255, 32, 255, 255, 255]
    if buf is None:
        buf = _np.empty(magpat.shape + (3,), _c.c_uint8)
    else:
        assert buf.size == 3 * magpat.size
    if min_mag is None:
        min_mag = -1.0
    if max_mag is None:
        max_mag = -1.0
    assert len(colors) - 1 == len(steps)
    assert len(colors[0]) == 3
    colors_arr = _np.array(colors, dtype=_c.c_uint8)
    steps_arr = _np.array(list(steps) + [0], dtype=_c.c_uint)
    _render_magpat_gradient(magpat, buf, magpat.shape[1], magpat.shape[0],
                            min_mag, max_mag, colors_arr, steps_arr)
    return buf

_light_curve.argtypes = [_c.POINTER(MagpatParams),
                         _ndpointer(_c.c_float, flags="C_CONTIGUOUS"),
                         _ndpointer(_c.c_float, flags="C_CONTIGUOUS"),
                         _c.c_uint,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double]
_light_curve.restype = None

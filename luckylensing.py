import ctypes as _c
import numpy as _np
from numpy.ctypeslib import ndpointer as _ndpointer

_libll = _c.CDLL("./libll.so")
_shoot_single_ray = _libll.ll_shoot_single_ray
_rayshoot_rect = _libll.ll_rayshoot_rect
_get_subpatches = _libll.ll_get_subpatches
_rayshoot_subpatches = _libll.ll_rayshoot_subpatches
_rayshoot = _libll.ll_rayshoot
_ray_hit_pattern = _libll.ll_ray_hit_pattern
_source_images = _libll.ll_source_images
_render_magpattern_greyscale = _libll.ll_render_magpattern_greyscale
_light_curve = _libll.ll_light_curve

class Lens(_c.Structure):
    _fields_ = [("x", _c.c_double),
                ("y", _c.c_double),
                ("mass", _c.c_double)]

    def __repr__(self):
        return "%s.%s(%0.5g, %0.5g, %0.5g)" % (
            self.__class__.__module__, self.__class__.__name__,
            self.x, self.y, self.mass)

class Lenses(_c.Structure):
    _fields_ = [("num_lenses", _c.c_uint),
                ("lens", _c.POINTER(Lens))]

    def __init__(self, lens_list):
        l = len(lens_list)
        super(Lenses, self).__init__(l, (Lens*l)(*map(tuple, lens_list)))

class Rect(_c.Structure):
    _fields_ = [("x", _c.c_double),
                ("y", _c.c_double),
                ("width", _c.c_double),
                ("height", _c.c_double)]

    def __repr__(self):
        return "%s.%s(%0.5g, %0.5g, %0.5g, %0.5g)" % (
            self.__class__.__module__, self.__class__.__name__,
            self.x, self.y, self.width, self.height)

    def __setattr__(self, name, value):
        super(Rect, self).__setattr__(name, value)
        if getattr(self, "callback", None) and name in ("width", "height"):
            self.callback()

class Patches(_c.Structure):
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

    def __setattr__(self, name, value):
        if name in ("width_per_xrays", "height_per_yrays"):
            raise AttributeError, "Attribute %s is not writable" % name
        super(Patches, self).__setattr__(name, value)
        if name in ("rect", "xrays", "yrays"):
            self.update_ratios()

    def __getattribute__(self, name):
        value = super(Patches, self).__getattribute__(name)
        if name == "rect":
            value.callback = (super(Patches, self).
                              __getattribute__("update_ratios"))
        return value

    def update_ratios(self):
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
            self.update_ratios()

    def __getattribute__(self, name):
        value = super(MagPatternParams, self).__getattribute__(name)
        if name == "region":
            value.callback = (super(MagPatternParams, self).
                              __getattribute__("update_ratios"))
        return value

    def update_ratios(self):
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

    rayshoot_rect = _rayshoot_rect
    ray_hit_pattern = _ray_hit_pattern
    source_images = _source_images
    light_curve = _light_curve

Progress = _c.c_double

class Rayshooter(_c.Structure):
    _fields_ = [("params", _c.POINTER(MagPatternParams)),
                ("levels", _c.c_uint),
                ("refine", _c.c_int),
                ("refine_final", _c.c_int),
                ("cancel_flag", _c.c_int)]

    def __init__(self, params, levels):
        if type(params) is not MagPatternParams:
            params = MagPatternParams(*params)
        super(Rayshooter, self).__init__(_c.pointer(params), levels, 15, 25, False)

    def cancel(self):
        self.cancel_flag = True

    def get_subpatches(self, patches):
        _get_subpatches(self.params, patches)

    def start_subpatches(self, magpat, patches, progress=Progress()):
        self.cancel_flag = False
        _rayshoot_subpatches(self, magpat, patches, self.levels - 1, progress)

    def start(self, magpat, rect, xrays, yrays, progress=Progress()):
        self.cancel_flag = False
        _rayshoot(self, magpat, rect, xrays, yrays, progress)

_shoot_single_ray.argtypes = [_c.POINTER(MagPatternParams),
                              _c.c_double,
                              _c.c_double,
                              _c.POINTER(_c.c_double),
                              _c.POINTER(_c.c_double)]
_shoot_single_ray.restype = _c.c_int

_rayshoot_rect.argtypes = [_c.POINTER(MagPatternParams),
                           _ndpointer(int),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int]
_rayshoot_rect.restype = None

_get_subpatches.argtypes = [_c.POINTER(MagPatternParams),
                            _c.POINTER(Patches)]
_get_subpatches.restype = None

_rayshoot_subpatches.argtypes = [_c.POINTER(Rayshooter),
                                 _ndpointer(int),
                                 _c.POINTER(Patches),
                                 _c.c_uint,
                                 _c.POINTER(_c.c_double)]
_rayshoot_subpatches.restype = None

_rayshoot.argtypes = [_c.POINTER(Rayshooter),
                      _ndpointer(int),
                      _c.POINTER(Rect),
                      _c.c_int,
                      _c.c_int,
                      _c.POINTER(_c.c_double)]
_rayshoot.restype = None

_ray_hit_pattern.argtypes = [_c.POINTER(MagPatternParams),
                             _ndpointer(_np.uint8),
                             _c.POINTER(Rect)]
_ray_hit_pattern.restype = None

_source_images.argtypes = [_c.POINTER(MagPatternParams),
                           _ndpointer(_np.uint8),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int,
                           _c.c_int,
                           _c.c_double,
                           _c.c_double,
                           _c.c_double]
_source_images.restype = None

_render_magpattern_greyscale.argtypes = [_ndpointer(_np.uint8),
                                         _ndpointer(int),
                                         _c.c_uint]
_render_magpattern_greyscale.restype = None

def render_magpattern_greyscale(buf, magpat):
    _render_magpattern_greyscale(buf, magpat, magpat.size)

_light_curve.argtypes = [_c.POINTER(MagPatternParams),
                         _ndpointer(int),
                         _ndpointer(float),
                         _c.c_uint,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double]
_light_curve.restype = None

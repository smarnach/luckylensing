import ctypes as _c
import numpy as _np

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
        super(Patches, self).__init__(
            rect, xrays, yrays, rect.width/xrays, rect.height/yrays,
            hit.ctypes.data_as(_c.POINTER(_c.c_char)), 0)

class MagPatternParams(_c.Structure):
    _fields_ = [("lenses", Lenses),
                ("region", Rect),
                ("xpixels", _c.c_uint),
                ("ypixels", _c.c_uint),
                ("pixels_per_width", _c.c_double),
                ("pixels_per_height", _c.c_double)]

    def __init__(self, lenses=[], region=(-1.,-1.,1.,1.),
                 xpixels=1024, ypixels=1024):
        super(MagPatternParams, self).__init__(Lenses(lenses), region,
                                               xpixels, ypixels)
        self.update_ratios()

    def update_ratios(self):
        self.pixels_per_width = self.xpixels / self.region.width
        self.pixels_per_height = self.ypixels / self.region.width

    def shoot_single_ray(self, x, y):
        mag_x = _c.c_double()
        mag_y = _c.c_double()
        b = bool(_shoot_single_ray(self, x, y, mag_x, mag_y))
        return mag_x.value, mag_y.value, b

    def rayshoot_rect(self, magpat, rect, xrays, yrays):
        _rayshoot_rect(self, magpat.ctypes.data_as(_c.POINTER(_c.c_int)),
                       rect, xrays, yrays)

    def ray_hit_pattern(self, buf, rect):
        _ray_hit_pattern(self, buf.ctypes.data_as(_c.POINTER(_c.c_char)), rect)

    def source_images(self, buf, rect, xrays, yrays, refine,
                      source_x, source_y, source_r):
        _source_images(self, buf.ctypes.data_as(_c.POINTER(_c.c_char)), rect,
                       xrays, yrays, refine, source_x, source_y, source_r)

    def light_curve(self, magpat, curve, num_points, x0, y0, x1, y1):
        _light_curve(self, magpat.ctypes.data_as(_c.POINTER(_c.c_int)),
                     curve.ctypes.data_as(_c.POINTER(_c.c_double)),
                     num_points, x0, y0, x1, y1)

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
        self.progress = []

    def cancel(self):
        self.cancel_flag = True

    def set_refine(refine):
        self.refine = refine

    def set_refine_final(refine_final):
        self.refine_final = refine_final

    def get_progress(self):
        l = len(self.progress)
        if l:
            return sum(p.value for p in self.progress) / l
        else:
            return 1.0

    def get_subpatches(self, patches):
        _get_subpatches(self.params, patches)

    def start_subpatches(self, magpat, patches):
        self.cancel_flag = False
        progress = _c.c_double(0.0)
        self.progress.append(progress)
        self.params[0].update_ratios()
        _rayshoot_subpatches(self, magpat.ctypes.data_as(_c.POINTER(_c.c_int)),
                             patches, self.levels - 1, progress)
        self.progress.remove(progress)

    def start(self, magpat, rect, xrays, yrays):
        self.cancel_flag = False
        progress = _c.c_double(0.0)
        self.progress.append(progress)
        self.params[0].update_ratios()
        _rayshoot(self, magpat.ctypes.data_as(_c.POINTER(_c.c_int)),
                  rect, xrays, yrays, progress)
        self.progress.remove(progress)

_libll = _np.ctypeslib.load_library('libll', '.')

_shoot_single_ray = _libll.ll_shoot_single_ray
_shoot_single_ray.argtypes = [_c.POINTER(MagPatternParams),
                              _c.c_double,
                              _c.c_double,
                              _c.POINTER(_c.c_double),
                              _c.POINTER(_c.c_double)]
_shoot_single_ray.restype = _c.c_int

_rayshoot_rect = _libll.ll_rayshoot_rect
_rayshoot_rect.argtypes = [_c.POINTER(MagPatternParams),
                           _c.POINTER(_c.c_int),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int]

_get_subpatches = _libll.ll_get_subpatches
_get_subpatches.argtypes = [_c.POINTER(MagPatternParams),
                            _c.POINTER(Patches)]

_rayshoot_subpatches = _libll.ll_rayshoot_subpatches
_rayshoot_subpatches.argtypes = [_c.POINTER(Rayshooter),
                                 _c.POINTER(_c.c_int),
                                 _c.POINTER(Patches),
                                 _c.c_uint,
                                 _c.POINTER(_c.c_double)]

_rayshoot = _libll.ll_rayshoot
_rayshoot.argtypes = [_c.POINTER(Rayshooter),
                      _c.POINTER(_c.c_int),
                      _c.POINTER(Rect),
                      _c.c_int,
                      _c.c_int,
                      _c.POINTER(_c.c_double)]

_ray_hit_pattern = _libll.ll_ray_hit_pattern
_ray_hit_pattern.argtypes = [_c.POINTER(MagPatternParams),
                             _c.POINTER(_c.c_char),
                             _c.POINTER(Rect)]

_source_images = _libll.ll_source_images
_source_images.argtypes = [_c.POINTER(MagPatternParams),
                           _c.POINTER(_c.c_char),
                           _c.POINTER(Rect),
                           _c.c_int,
                           _c.c_int,
                           _c.c_int,
                           _c.c_double,
                           _c.c_double,
                           _c.c_double]

_render_magpattern_greyscale = _libll.ll_render_magpattern_greyscale
_render_magpattern_greyscale.argtypes = [_c.POINTER(_c.c_char),
                               _c.POINTER(_c.c_int),
                               _c.c_uint]

def render_magpattern_greyscale(buf, magpat):
    _render_magpattern_greyscale(buf.ctypes.data_as(_c.POINTER(_c.c_char)),
                                 magpat.ctypes.data_as(_c.POINTER(_c.c_int)),
                                 magpat.size)

_light_curve = _libll.ll_light_curve
_light_curve.argtypes = [_c.POINTER(MagPatternParams),
                         _c.POINTER(_c.c_int),
                         _c.POINTER(_c.c_double),
                         _c.c_uint,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double,
                         _c.c_double]
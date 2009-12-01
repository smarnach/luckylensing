import ctypes as _c

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
        self.pixels_per_width = xpixels / self.region.width
        self.pixels_per_height = ypixels / self.region.width

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

    def start(self, magpat, rect, xrays, yrays):
        self.cancel_flag = False
        self.progress.append(_c.c_double(0.0))
        _rayshoot(self, magpat.ctypes.data_as(_c.POINTER(_c.c_int)),
                  rect, xrays, yrays, self.progress[-1])
        self.progress.pop()

from numpy import ctypeslib as _ctypeslib
_libll = _ctypeslib.load_library('libll', '.')

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

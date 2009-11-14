import numpy
import ctypes as c

class Lens(c.Structure):
    _fields_ = [("x", c.c_double),
                ("y", c.c_double),
                ("theta_E", c.c_double)]

class Lenses(c.Structure):
    _fields_ = [("num_lenses", c.c_uint),
               ("lens", c.POINTER(Lens))]
    def __init__(self, lens_list):
        l = len(lens_list)
        super(Lenses, self).__init__(l, (Lens*l)(*map(tuple, lens_list)))

class Rect(c.Structure):
    _fields_ = [("x0", c.c_double),
                ("y0", c.c_double),
                ("x1", c.c_double),
                ("y1", c.c_double)]

class MagPatternParams(c.Structure):
    _fields_ = [("lenses", Lenses),
                ("region", Rect),
                ("xpixels", c.c_uint),
                ("ypixels", c.c_uint),
                ("pixels_per_width", c.c_double),
                ("pixels_per_height", c.c_double)]
    def __init__(self, lenses, region, xpixels, ypixels):
        super(MagPatternParams, self).__init__(Lenses(lenses), region,
                                               xpixels, ypixels)
        self.pixels_per_width = xpixels / (self.region.x1 - self.region.x0)
        self.pixels_per_height = ypixels / (self.region.y1 - self.region.y0)

class Rayshooter(c.Structure):
    _fields_ = [("params", c.POINTER(MagPatternParams)),
                ("refine", c.c_int),
                ("refine_final", c.c_int),
                ("cancel", c.c_int)]

    def __init__(self, params):
        self.params = c.pointer(params)
        self.refine = 15
        self.refine_final = 25
        self.cancel = False
        self.progress = []

    def cancel(self):
        self.cancel = True

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

    def start(self, magpat, rect, xrays, yrays, levels):
        self.progress.append(c.c_double(0.0))
        _rayshoot(self, magpat.ctypes.data_as(c.POINTER(c.c_int)),
                  rect, xrays, yrays, levels, self.progress[-1])
        self.progress.pop()

_libll = numpy.ctypeslib.load_library('libll', '.')

_rayshoot_rect = _libll.ll_rayshoot_rect
_rayshoot_rect.argtypes = [c.POINTER(MagPatternParams),
                           c.POINTER(c.c_int),
                           c.POINTER(Rect),
                           c.c_int,
                           c.c_int]

def rayshoot_rect(params, magpat, rect, xrays, yrays):
    _rayshoot_rect(params, magpat.ctypes.data_as(c.POINTER(c.c_int)),
                   rect, xrays, yrays)

_rayshoot = _libll.ll_rayshoot
_rayshoot.argtypes = [c.POINTER(Rayshooter),
                      c.POINTER(c.c_int),
                      c.POINTER(Rect),
                      c.c_int,
                      c.c_int,
                      c.c_uint,
                      c.POINTER(c.c_double)]

_image_from_magpat = _libll.ll_image_from_magpat
_image_from_magpat.argtypes = [c.POINTER(c.c_char),
                               c.POINTER(c.c_int),
                               c.c_uint]

def image_from_magpat(buf, magpat):
    _image_from_magpat(buf.ctypes.data_as(c.POINTER(c.c_char)),
                       magpat.ctypes.data_as(c.POINTER(c.c_int)),
                       magpat.size)

_light_curve = _libll.ll_light_curve
_light_curve.argtypes = [c.POINTER(MagPatternParams),
                         c.POINTER(c.c_int),
                         c.POINTER(c.c_double),
                         c.c_uint,
                         c.c_double,
                         c.c_double,
                         c.c_double,
                         c.c_double]

def light_curve(params, magpat, curve, num_points, x0, y0, x1, y1):
    _light_curve(params, magpat.ctypes.data_as(c.POINTER(c.c_int)),
                 curve.ctypes.data_as(c.POINTER(c.c_double)),
                 num_points, x0, y0, x1, y1)

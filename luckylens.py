import numpy
import ctypes

class Lens(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double),
                ("y", ctypes.c_double),
                ("theta_E", ctypes.c_double)]

class Lenses(ctypes.Structure):
    _fields_ = [("num_lenses", ctypes.c_uint),
               ("lens", ctypes.POINTER(Lens))]
    def __init__(self, lens_list):
        l = len(lens_list)
        super(Lenses, self).__init__(l, (Lens*l)(*map(tuple, lens_list)))

class Rect(ctypes.Structure):
    _fields_ = [("x0", ctypes.c_double),
                ("y0", ctypes.c_double),
                ("x1", ctypes.c_double),
                ("y1", ctypes.c_double)]

class MagPatternParams(ctypes.Structure):
    _fields_ = [("lenses", Lenses),
                ("region", Rect),
                ("xpixels", ctypes.c_uint),
                ("ypixels", ctypes.c_uint),
                ("pixels_per_width", ctypes.c_double),
                ("pixels_per_height", ctypes.c_double)]
    def __init__(self, lenses, region, xpixels, ypixels):
        super(MagPatternParams, self).__init__(Lenses(lenses), region,
                                               xpixels, ypixels)
        self.pixels_per_width = xpixels / (self.region.x1 - self.region.x0)
        self.pixels_per_height = ypixels / (self.region.y1 - self.region.y0)

_libll = numpy.ctypeslib.load_library('libll', '.')

_rayshoot_rect = _libll.ll_rayshoot_rect
_rayshoot_rect.argtypes = [ctypes.POINTER(MagPatternParams),
                           ctypes.POINTER(ctypes.c_int),
                           ctypes.POINTER(Rect),
                           ctypes.c_int,
                           ctypes.c_int]

def rayshoot_rect(params, magpat, rect, xrays, yrays):
    _rayshoot_rect(params, magpat.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                   rect, xrays, yrays)

_rayshoot = _libll.ll_rayshoot
_rayshoot.argtypes = [ctypes.POINTER(MagPatternParams),
                      ctypes.POINTER(ctypes.c_int),
                      ctypes.POINTER(Rect),
                      ctypes.c_int,
                      ctypes.c_int,
                      ctypes.c_uint,
                      ctypes.POINTER(ctypes.c_double)]

Progress = ctypes.c_double

def rayshoot(params, magpat, rect, xrays, yrays, levels, progress):
    _rayshoot(params, magpat.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
              rect, xrays, yrays, levels, progress)

_image_from_magpat = _libll.ll_image_from_magpat
_image_from_magpat.argtypes = [ctypes.POINTER(ctypes.c_char),
                               ctypes.POINTER(ctypes.c_int),
                               ctypes.c_uint]

def image_from_magpat(buf, magpat):
    _image_from_magpat(buf.ctypes.data_as(ctypes.POINTER(ctypes.c_char)),
                       magpat.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
                       numpy.prod(magpat.shape))

import numpy
import ctypes

class Lens(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double),
                ("y", ctypes.c_double),
                ("theta_E", ctypes.c_double)]

class Lenses(ctypes.Structure):
    _fields_ = [("num_lenses", ctypes.c_uint),
               ("lens", ctypes.POINTER(Lens))]

class Rect(ctypes.Structure):
    _fields_ = [("x0", ctypes.c_double),
                ("y0", ctypes.c_double),
                ("x1", ctypes.c_double),
                ("y1", ctypes.c_double)]

class MagPattern(ctypes.Structure):
    _fields_ = [("lenses", Lenses),
                ("region", Rect),
                ("xpixels", ctypes.c_uint),
                ("ypixels", ctypes.c_uint),
                ("pixels_per_width", ctypes.c_double),
                ("pixels_per_height", ctypes.c_double),
                ("count", ctypes.POINTER(ctypes.c_int))]

def new_MagPattern(*args):
    m = MagPattern(*args[:-1])
    m.count = args[-1].ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    return m

libll = numpy.ctypeslib.load_library('libll', '.')

rayshoot_rect = libll.ll_rayshoot_rect
rayshoot_rect.argtypes = [ctypes.POINTER(MagPattern),
                          ctypes.POINTER(Rect),
                          ctypes.c_int,
                          ctypes.c_int]

rayshoot = libll.ll_rayshoot
rayshoot.argtypes = [ctypes.POINTER(MagPattern),
                     ctypes.POINTER(Rect),
                     ctypes.c_int,
                     ctypes.c_int,
                     ctypes.c_uint,
                     ctypes.POINTER(ctypes.c_double)]

Progress = ctypes.c_double

_image_from_magpat = libll.ll_image_from_magpat
_image_from_magpat.argtypes = [ctypes.POINTER(ctypes.c_char),
                               ctypes.POINTER(MagPattern)]

def image_from_magpat(buf, magpat):
    _image_from_magpat(buf.ctypes.data_as(ctypes.POINTER(ctypes.c_char)),
                       magpat)

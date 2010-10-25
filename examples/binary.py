#!/usr/bin/env python

import sys
sys.path.append("..")

from luckylensing import Rayshooter
from imagewriter import ImageWriter
from math import log
from subprocess import call
import numpy

x_values = 0.6 + 0.1*numpy.arange(12)
mass_values = 1. / 10.**(0.5*numpy.arange(7))

pipe = [Rayshooter(), ImageWriter()]
for j, mass in enumerate(mass_values):
    for i, x in enumerate(x_values):
        data = dict(
            # Lens configuration
            lenses = [(0., 0., 1.), (x, 0., mass)],
            # Parameters for the ray shooter:
            density = 1000,
            kernel = "triangulated",
            num_threads = 2,
            xpixels = 256,
            ypixels = 256,
            region_x0 = -0.5,
            region_y0 = -1.,
            region_x1 =  1.5,
            region_y1 =  1.,
            # Parameters for the image file writer:
            min_mag = 1.0,
            max_mag = 120.0,
            imgfile = "binary-%02i-%02i.png" % (j, i))
        for processor in pipe:
            processor.update(data)

s = call("montage binary-??-??.png -geometry +8+8 -tile %ix " % len(x_values) +
         "-background black magpats/binary.png", shell=True)
if not s:
    call("rm binary-??-??.png", shell=True)

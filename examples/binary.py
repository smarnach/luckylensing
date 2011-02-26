#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from luckylensing import Rayshooter, pipeline
from imagewriter import save_img
from subprocess import call
import numpy

x_values = 0.6 + 0.1*numpy.arange(12)
mass_values = 1. / 10.**(0.5*numpy.arange(7))

pipe = pipeline.Pipeline(Rayshooter, save_img)
for j, mass in enumerate(mass_values):
    for i, x in enumerate(x_values):
        pipe.run(
            # Lens configuration
            lenses = [(0., 0., 1.), (x, 0., mass)],
            # Parameters for the ray shooter:
            region = (-0.5, -1., 1.5, 1.),
            xpixels = 256,
            ypixels = 256,
            density = 1000,
            num_threads = 2,
            # Parameters for the image file writer:
            min_mag = 1.0,
            max_mag = 120.0,
            imgfile = "binary-%02i-%02i.png" % (j, i))

s = call("montage binary-??-??.png -geometry +8+8 -tile %ix " % len(x_values) +
         "-background black magpats/binary.png", shell=True)
if not s:
    call("rm binary-??-??.png", shell=True)

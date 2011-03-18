#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from luckylensing import rayshoot
from PIL import Image
import numpy

# Parameters to control the output ####
x_values = 0.6 + 0.1*numpy.arange(12)
mass_values = 1. / 10.**(0.5*numpy.arange(7))
region = (-0.5, -1.0, 1.5, 1.0)
xpixels = ypixels = 256
margin = 8
imgfile = "magpats/binary.png"
#######################################

shape = (len(mass_values) * (ypixels + 2 * margin),
         len(x_values) * (ypixels + 2 * margin), 3)
buf = numpy.zeros(shape, numpy.uint8)
for j, mass in enumerate(mass_values):
    for i, x in enumerate(x_values):
        print "Ray shooting for mass ratio %.2e and distance %.2f" % (mass, x)
        sys.stdout.write("\033[F") # Cursor up one line
        lenses = [(0.0, 0.0, 1.0), (x, 0.0, mass)]
        magpat = rayshoot(lenses, region, xpixels, ypixels,
                          density=1000, num_threads=2, verbose=0)
        j0 = j * (ypixels + 2 * margin)
        i0 = i * (xpixels + 2 * margin)
        buf[j0:j0+ypixels, i0:i0+xpixels] = magpat.render_gradient(
            min_mag=1.0, max_mag=120.0)
sys.stdout.write("\033[K") # Clear to the end of line
print "Writing magnification patterns to", imgfile
Image.fromarray(buf).save(imgfile)
print "Done."

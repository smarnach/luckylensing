#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from luckylensing import GlobularCluster, Rayshooter
from imagewriter import ImageWriter
from math import log

pipe = [GlobularCluster(), Rayshooter(), ImageWriter()]
for i in range(1000):
    log_mass = -8.0 + 0.005*i
    data = dict(
        # Parameters for the cluster generator:
        num_stars = 1000,
        total_mass = 1000 * exp(log_mass),
        random_seed = 43,
        # Parameters for the ray shooter:
        density = 15 * 1.5**(-log_mass),
        kernel = "bilinear",
        num_threads = 2,
        xpixels = 1024,
        ypixels = 768,
        region_x0 = -1.6,
        region_y0 = -1.2,
        region_x1 = 1.6,
        region_y1 = 1.2,
        # Parameters for the image file writer:
        min_mag = 1.2,
        max_mag = 150.0,
        imgfile = "magpats/collapse-%04i.png" % i)
    for processor in pipe:
        processor.update(data)

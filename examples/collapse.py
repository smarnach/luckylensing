#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from luckylensing import pipeline, globular_cluster, Rayshooter
from imagewriter import save_img
from math import log, exp

pipe = pipeline.Pipeline(globular_cluster, Rayshooter, save_img)
for i in range(1000):
    log_mass = -8.0 + 0.005*i
    pipe.run(
        # Parameters for the cluster generator:
        num_stars = 1000,
        total_mass = 1000 * exp(log_mass),
        random_seed = 43,
        # Parameters for the ray shooter:
        region = (-1.6, -1.2, 1.6, 1.2),
        xpixels = 1024,
        ypixels = 768,
        density = 15 * 1.5**(-log_mass),
        num_threads = 2,
        # Parameters for the image file writer:
        min_mag = 1.2,
        max_mag = 150.0,
        imgfile = "magpats/collapse-%04i.png" % i)

#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from luckylensing import rayshoot
from imagewriter import save_img

for i in range(120):
    lenses = [(0., 0., 1.), (0.8 + i*0.005, 0., .0025)]
    region = (-.4, -.25, .6, .25)
    magpat = rayshoot(lenses, region, 1024, 512, num_threads=2)
    save_img(magpat, "magpats/planet-%03i.png" % i,
             min_mag=3.0, max_mag=3000.0)

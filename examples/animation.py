#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter

for i in range(81):
    x = 0.8 + i*0.005
    p = ll.MagPatternParams([(0,0,1), (x, 0, .0004)], (-.5, -.25, 1, .5),
                            1024, 512)
    rs = Rayshooter(p)
    rs.start()
    ll.render_magpattern_greyscale(rs.count).tofile("magpats/magpat-%03i" % i)

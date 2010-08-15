#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter

colors = [(0, 0, 0), (0, 0, 0), (0, 0, 255), (32, 0, 255),
          (255, 0, 0), (255, 255, 0), (255, 255, 255)]
steps = [128, 512, 64, 255, 255, 512]

for i in range(101):
    x = 0.8 + i*0.004
    p = ll.MagPatternParams([(0,0,1), (x, 0, .0004)], (-.5, -.25, 1, .5),
                            1024, 512)
    rs = Rayshooter(p)
    rs.start()
    buf = ll.render_magpattern_gradient(rs.count, colors, steps)
    buf.tofile("magpats/magpat-%03i" % i)

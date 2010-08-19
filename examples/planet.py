#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter
from exampletools import save_png, colors, steps

for i in range(101):
    x = 0.85 + i*0.003
    p = ll.MagPatternParams([(0,0,1), (x, 0, .0004)], (-.3, -.15, .6, .3),
                            1024, 512)
    rs = Rayshooter(p)
    rs.run()
    buf = ll.render_magpattern_gradient(rs.count, colors, steps, 3.0, 3000.0)
    save_png(buf, "magpats/planet-%03i.png" % i)

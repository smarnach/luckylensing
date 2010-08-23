#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter
from ImageWriter import save_img, colors, steps

for i in range(101):
    x = 0.85 + i*0.003
    p = ll.MagPatternParams([(0,0,1), (x, 0, .0004)], (-.3, -.15, .6, .3),
                            1024, 512)
    rs = Rayshooter(p)
    rs.num_threads = 2
    rs.run()
    buf = ll.render_magpattern_gradient(rs.magpat, colors, steps, 3.0, 3000.0)
    save_img(buf, "magpats/planet-%03i.png" % i)

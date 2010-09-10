#!/usr/bin/env python

import sys
sys.path.append("..")

import luckylensing as ll
from imagewriter import save_img, colors, steps

for i in range(120):
    x = 0.8 + i*0.005
    p = ll.MagPatternParams([(0,0,1), (x, 0, .0025)], (-.4, -.25, 1., .5),
                            1024, 512)
    rs = ll.Rayshooter(p)
    rs.num_threads = 2
    rs.run()
    buf = ll.render_magpattern_gradient(rs.magpat, colors, steps, 3.0, 3000.0)
    save_img(buf, "magpats/planet-%03i.png" % i)

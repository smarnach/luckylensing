#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter
from exampletools import save_png, colors, steps, get_ints_from_files
import numpy as np
from math import pi, sin, cos

N = 1000
np.random.seed(47)
coords = np.random.multivariate_normal([0., 0., 0.], np.identity(3), N)
masses = np.random.lognormal(-7, 0.1, (N, 1))

p = ll.MagPatternParams([], (-.3, -.225, .6, .45), 1024, 768)
rs = Rayshooter(p)
rs.kernel = ll.KERNEL_TRIANGULATED
rs.density = 625

if len(sys.argv) > 1:
    frames = get_ints_from_files(sys.argv[1:])
else:
    frames = range(3000)
for i in frames:
    alpha = 0.0005 * i
    lenses = np.hstack((cos(alpha) * coords[:,:1] + sin(alpha) * coords[:,1:2],
                        coords[:,2:], masses))
    p.lenses = ll.Lenses(lenses)
    rs.start()
    buf = ll.render_magpattern_gradient(rs.count, colors, steps, 1.0, 100.0)
    save_png(buf, "magpats/cluster-%04i.png" % i)

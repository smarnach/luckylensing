#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter
from exampletools import save_png, colors, steps
import numpy as np
from math import pi, sin, cos

N = 1000
np.random.seed(42)
coords = np.random.multivariate_normal([0., 0., 0.], np.identity(3), N)
masses = np.random.lognormal(-7, 0.1, (N, 1))

p = ll.MagPatternParams([], (-1., -1., 2., 2.), 1024, 1024)
rs = Rayshooter(p)
rs.kernel = ll.KERNEL_BILINEAR
rs.density = 100

i = 0
for alpha in np.arange(0.0, 0.25*pi, 0.001):
    lenses = np.hstack((cos(alpha) * coords[:,:1] + sin(alpha) * coords[:,1:2],
                        coords[:,2:], masses))
    p.lenses = ll.Lenses(lenses)
    rs.start()
    buf = ll.render_magpattern_gradient(rs.count, colors, steps)
    save_png(buf, "magpats/cluster-%04i.png" % i)
    i += 1
    break

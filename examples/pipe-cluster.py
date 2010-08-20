#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter
from globularcluster import GlobularCluster
from exampletools import save_png, colors, steps

data = {"region_radius": 1.0,
        "kernel": ll.KERNEL_BILINEAR,
        "density": 500,
        "num_threads": 2}
pipe = [GlobularCluster(), Rayshooter()]
for processor in pipe:
    processor.update(data)
buf = ll.render_magpattern_gradient(data["magpat"], colors, steps, 1.0, 50.0)
save_png(buf, "magpats/pipe-cluster.png")

#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from pipeline import Pipeline
from rayshooter import Rayshooter
from globularcluster import GlobularCluster
from exampletools import save_png, colors, steps

pipe = Pipeline([GlobularCluster(), Rayshooter()])
data = {"region_radius": 1.0,
        "kernel": ll.KERNEL_BILINEAR,
        "density": 500,
        "num_threads": 2}
pipe.run(data)
buf = ll.render_magpattern_gradient(data["magpat"], colors, steps, 1.0, 50.0)
save_png(buf, "magpats/pipe-cluster.png")

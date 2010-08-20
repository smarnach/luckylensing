#!/usr/bin/env python

import sys
sys.path.append("../libll")

import luckylensing as ll
from rayshooter import Rayshooter
from globularcluster import GlobularCluster
from argsparser import ArgsParser
from exampletools import save_png, colors, steps

data = {"args": sys.argv[1:],
        "num_threads": 2}
pipe = [ArgsParser(), GlobularCluster(), Rayshooter()]
for processor in pipe:
    processor.update(data)
buf = ll.render_magpattern_gradient(data["magpat"], colors, steps, 1.0, 50.0)
save_png(buf, "magpats/pipe-cluster.png")

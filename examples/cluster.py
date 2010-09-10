#!/usr/bin/env python

import sys
sys.path.append("..")

from argsparser import ArgsParser
from luckylensing import GlobularCluster, Rayshooter
from imagewriter import ImageWriter

data = {"args": sys.argv[1:],
        "num_threads": 2}
pipe = [ArgsParser(), GlobularCluster(), Rayshooter(), ImageWriter()]
for processor in pipe:
    processor.update(data)

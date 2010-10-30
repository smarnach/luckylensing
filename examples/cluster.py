#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from argsparser import ArgsParser
from luckylensing import GlobularCluster, Rayshooter, FITSWriter
from imagewriter import ImageWriter

data = {"args": sys.argv[1:],
        "num_threads": 2}
pipe = [ArgsParser(), GlobularCluster(), Rayshooter(),
        FITSWriter(), ImageWriter()]
for processor in pipe:
    processor.update(data)

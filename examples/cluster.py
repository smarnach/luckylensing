#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from argsparser import parse_args
from luckylensing import pipeline, globular_cluster, Rayshooter
from imagewriter import save_img

pipe = pipeline.Pipeline(parse_args, globular_cluster, Rayshooter, save_img)
pipe.run(args=sys.argv[1:], num_threads=2)

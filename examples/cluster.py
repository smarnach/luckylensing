#!/usr/bin/env python
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import sys
sys.path.append("..")

from luckylensing import pipeline, globular_cluster, Rayshooter
from imagewriter import save_img

def parse_args(args):
    """Parse command line arguments in the format "key=value".

    The function returns a dictionary of the key/value pairs.  Values
    are evaluated as Python expressions using eval() if possible.
    """
    output = {}
    for arg in args:
        key, value = arg.split("=", 1)
        try:
            value = eval(value)
        except Exception:
            pass
        output[key] = value
    return output

pipe = pipeline.Pipeline(parse_args, globular_cluster, Rayshooter, save_img)
pipe.run(args=sys.argv[1:], num_threads=2)

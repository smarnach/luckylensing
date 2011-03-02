#!/bin/sh
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

for i in `seq 0 3141`; do
    ./cluster.py imgfile="magpats/cluster-$(printf %04i $i).png" \
        kernel=bilinear density=500 xpixels=1024 ypixels=768 \
        region="(-0.3, -0.225, 0.3, 0.225)" \
        random_seed=47 angle="0.0005*$i" min_mag=1.25 max_mag=60.0
done

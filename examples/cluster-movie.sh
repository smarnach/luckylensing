#!/bin/sh

for i in `seq 0 3141`; do
    ./cluster.py imgfile="magpats/cluster-$(printf %04i $i).png" \
        kernel=bilinear density=500 xpixels=1024 ypixels=768 \
        region_x0=-0.3 region_y0=-0.225 region_x1=0.3 region_y1=0.225 \
        random_seed=47 angle="eval(0.0005*$i)" min_mag=1.25 max_mag=60.0
done

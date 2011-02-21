# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import libll as ll
from processor import Processor
import numpy

class LightCurve(Processor):
    def get_input_keys(self, data):
        return ["magpat",
                "region_x0", "region_x1", "region_y0", "region_y1",
                "curve_x0", "curve_x1", "curve_y0", "curve_y1",
                "curve_samples"]

    def run(self, data):
        magpat = data["magpat"]
        region_x0 = data["region_x0"]
        region_x1 = data["region_x1"]
        region_y0 = data["region_y0"]
        region_y1 = data["region_y1"]
        region = (region_x0, region_y0, region_x1 - region_x0,
                  region_y1 - region_y0)
        ypixels, xpixels = magpat.shape
        params = ll.MagpatParams([], region, xpixels, ypixels)
        samples = data.get("curve_samples", 256)
        curve = numpy.empty(samples, dtype=numpy.float32)
        params.light_curve(magpat, curve, data["curve_x0"], data["curve_y0"],
                           data["curve_x1"], data["curve_y1"])
        return {"light_curve": curve}

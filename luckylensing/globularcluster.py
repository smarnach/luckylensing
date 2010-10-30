# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import numpy
from math import pi, sin, cos, log
from processor import Processor

class GlobularCluster(Processor):
    def get_input_keys(self, data):
        return ["num_stars", "random_seed", "total_mass", "log_mass_stddev",
                "angle", "region_radius"]

    def run(self, data):
        num_stars = data.get("num_stars", 1000)
        random_seed = data.get("random_seed", 42)
        total_mass = data.get("total_mass", 1.0)
        log_mass_stddev = data.get("log_mass_stddev", 0.0)
        angle = data.get("angle", 0.0)
        region_radius = data.get("region_radius", 1.0)
        numpy.random.seed(random_seed)
        coords = numpy.random.multivariate_normal([0., 0., 0.],
                                                  numpy.identity(3),
                                                  num_stars)
        coords -= coords.mean(axis=0)
        if log_mass_stddev <= 0.0:
            masses = numpy.ones((num_stars, 1)) * (total_mass / num_stars)
        else:
            masses = numpy.random.lognormal(log(total_mass / num_stars),
                                            log_mass_stddev * log(10.0),
                                            (num_stars, 1))
            masses *= total_mass / num_stars / masses.mean()
        lenses = numpy.hstack((cos(angle) * coords[:,:1] +
                               sin(angle) * coords[:,1:2],
                               coords[:,2:], masses))
        output = {"lenses": numpy.ascontiguousarray(lenses)}
        if region_radius > 0.0:
            if "region_radius" not in data:
                for k in ["region_x0", "region_x1", "region_y0", "region_y1"]:
                    if k in data:
                        return output
            output["region_x0"] = -region_radius
            output["region_y0"] = -region_radius
            output["region_x1"] = +region_radius
            output["region_y1"] = +region_radius
        return output

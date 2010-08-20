import numpy
from math import pi, sin, cos
from processor import Processor
from luckylensing import Lenses

class GlobularCluster(Processor):
    def get_input_keys(self, data):
        return ["num_stars", "random_seed", "log_mass", "log_mass_stddev",
                "angle", "region_radius"]

    def run(self, data):
        num_stars = data.get("num_stars", 1000)
        random_seed = data.get("random_seed", 42)
        log_mass = data.get("log_mass", -7.0)
        log_mass_stddev = data.get("log_mass_stddev", 0.1)
        angle = data.get("angle", 0.0)
        region_radius = data.get("region_radius", 1.0)
        numpy.random.seed(random_seed)
        coords = numpy.random.multivariate_normal([0., 0., 0.],
                                                  numpy.identity(3),
                                                  num_stars)
        masses = numpy.random.lognormal(log_mass, log_mass_stddev,
                                        (num_stars, 1))
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

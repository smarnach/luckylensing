import numpy
from math import pi, sin, cos
from processor import Processor
from luckylensing import Lenses

class GlobularCluster(Processor):
    def __init__(self):
        super(GlobularCluster, self).__init__()
        self.num_stars = 1000
        self.random_seed = 42
        self.log_mass = -7.0
        self.log_mass_stddev = 0.1
        self.angle = 0.0
        self.region_radius = None

    def get_input_keys(self, data):
        return ["num_stars", "random_seed", "log_mass", "log_mass_stddev",
                "angle", "region_radius"]

    def get_output_keys(self, data):
        if data.get("region_radius"):
            return ["lenses", "region_x0", "region_x1",
                    "region_y0", "region_y1"]
        return ["lenses"]

    def run(self, data):
        for key in self.get_input_keys(data):
            if data.has_key(key):
                setattr(self, key, data[key])
        numpy.random.seed(self.random_seed)
        coords = numpy.random.multivariate_normal([0., 0., 0.],
                                                  numpy.identity(3),
                                                  self.num_stars)
        masses = numpy.random.lognormal(self.log_mass, self.log_mass_stddev,
                                        (self.num_stars, 1))
        lenses = numpy.hstack((cos(self.angle) * coords[:,:1] +
                               sin(self.angle) * coords[:,1:2],
                               coords[:,2:], masses))
        outputs = {"lenses": numpy.ascontiguousarray(lenses)}
        if self.region_radius:
            outputs["region_x0"] = -self.region_radius
            outputs["region_y0"] = -self.region_radius
            outputs["region_x1"] = +self.region_radius
            outputs["region_y1"] = +self.region_radius
        return outputs

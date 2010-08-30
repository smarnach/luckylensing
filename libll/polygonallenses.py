import numpy
from processor import Processor
from luckylensing import Lenses

class PolygonalLenses(Processor):
    def get_input_keys(self, data):
        return ["num_stars", "total_mass", "angle", "region_radius"]

    def run(self, data):
        num_stars = data.get("num_stars", 5)
        total_mass = data.get("total_mass", 1.0)
        angle = data.get("angle", 0.0)
        region_radius = data.get("region_radius", 1.5)
        phis = numpy.arange(angle, angle + 2.*numpy.pi, 2.*numpy.pi/num_stars)
        xcoords = numpy.cos(phis).reshape((num_stars, 1))
        ycoords = numpy.sin(phis).reshape((num_stars, 1))
        masses = numpy.ones((num_stars, 1)) * (total_mass / num_stars)
        lenses = numpy.hstack((xcoords, ycoords, masses))
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

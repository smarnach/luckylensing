import numpy
from processor import Processor
from math import sqrt

class SourceStar(Processor):
    def get_input_keys(self, data):
        return ["xpixels", "ypixels", "source_radius",
                "region_x0", "region_x1", "region_y0", "region_y1"]

    def run(self, data):
        xpixels = data["xpixels"]
        ypixels = data["ypixels"]
        assert xpixels % 2 == 0
        assert ypixels % 2 == 0
        source_radius = data.get("source_radius", 0.01)
        source_radius2 = source_radius*source_radius
        width = (data["region_x1"] - data["region_x0"]) / xpixels
        width2 = width*width
        height = (data["region_y1"] - data["region_y0"]) / ypixels
        height2 = height*height
        kernel = numpy.indices((ypixels/2, xpixels/2)) + 0.5
        kernel = kernel*kernel
        kernel = self.f(height2*kernel[0]+width2*kernel[1], source_radius2,
                        width, height)
        if kernel is None:
            return {"source_fft": None,
                    "source_profile": None}
        kernel = numpy.concatenate((kernel, numpy.flipud(kernel)), 0)
        kernel = numpy.concatenate((kernel, numpy.fliplr(kernel)), 1)
        kernel = kernel / float(numpy.sum(kernel))
        kernel_fft = numpy.fft.rfft2(kernel)
        return {"source_fft": kernel_fft,
                "source_profile": kernel}

class FlatSource(SourceStar):
    def f(self, r2, source_radius2, width, height):
        width2 = width*width
        height2 = height*height
        if source_radius2 <= 0.25*width2 + 0.25*height2:
            return None
        if source_radius2 <= 0.5*width2 + 0.5*height2:
            return r2 < source_radius2
        source_radius = sqrt(source_radius2)
        m = 1.0/((width+height)*source_radius)
        b = (source_radius2 +
             0.5*(width+height)*source_radius +
             0.25*width*height)
        return numpy.clip(-m*r2 + m*b, 0.0, 1.0)

class GaussianSource(SourceStar):
    def f(self, r2, source_radius2, width, height):
        return numpy.exp(-r2 / (2.0*source_radius2))

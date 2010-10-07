import numpy
from processor import Processor
from math import sqrt

class SourceProfile(Processor):
    def get_input_keys(self, data):
        return ["xpixels", "ypixels", "profile_type", "source_radius",
                "region_x0", "region_x1", "region_y0", "region_y1"]

    def run(self, data):
        xpixels = data["xpixels"]
        ypixels = data["ypixels"]
        source_radius = data.get("source_radius", 0.01)
        source_radius2 = source_radius*source_radius
        width = (data["region_x1"] - data["region_x0"]) / xpixels
        width2 = width*width
        height = (data["region_y1"] - data["region_y0"]) / ypixels
        height2 = height*height
        kernel = numpy.indices((ypixels//2 + 1, xpixels//2 + 1))
        kernel = kernel*kernel
        kernel = height2*kernel[0]+width2*kernel[1]
        profile_type = data.get("profile_type", "flat").lower()
        if profile_type == "flat":
            kernel = self.flat(kernel, source_radius2, width, height)
        elif profile_type == "gaussian":
            kernel = self.gaussian(kernel, source_radius2, width, height)
        else:
            raise ValueError("Unknown source profile type: " + profile_type)
        kernel = numpy.vstack((kernel[:-1], numpy.flipud(kernel[1:])))
        kernel = numpy.hstack((kernel[:,:-1], numpy.fliplr(kernel[:,1:])))
        kernel = kernel / float(numpy.sum(kernel))
        kernel_fft = numpy.fft.rfft2(kernel)
        return {"source_fft": kernel_fft,
                "source_profile": kernel}

    def flat(self, r2, source_radius2, width, height):
        width2 = width*width
        height2 = height*height
        if source_radius2 <= 0.25*width2 + 0.25*height2:
            return r2 <= source_radius2
        source_radius = sqrt(source_radius2)
        m = 1.0/((width+height)*source_radius)
        b = (source_radius2 +
             0.5*(width+height)*source_radius +
             0.25*width*height)
        return numpy.clip(-m*r2 + m*b, 0.0, 1.0)

    def gaussian(self, r2, source_radius2, width, height):
        return numpy.exp(-r2 / (2.0*source_radius2))

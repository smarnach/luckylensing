import numpy
from processor import Processor

class Convolution(Processor):
    def get_input_keys(self, data):
        return ["magpat", "source_fft"]

    def run(self, data):
        kernel_fft = data.get("source_fft")
        magpat = data["magpat"]
        if kernel_fft is None:
            return {"convolved_magpat": magpat}
        convolved_pattern = numpy.empty_like(magpat)
        convolved_pattern[:] = numpy.fft.irfft2(
            numpy.fft.rfft2(magpat) * kernel_fft)
        return {"convolved_magpat": convolved_pattern}

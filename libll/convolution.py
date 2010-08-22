import numpy
from processor import Processor

class Convolution(Processor):
    def get_input_keys(self, data):
        return ["magpat", "source_fft"]

    def run(self, data):
        magpat = data["magpat"]
        kernel_fft = data["source_fft"]
        convolved_pattern = numpy.empty_like(magpat)
        convolved_pattern[:] = numpy.fft.irfft2(
            numpy.fft.rfft2(magpat) * kernel_fft)
        return {"convolved_magpat": convolved_pattern}

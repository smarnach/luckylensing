import numpy
from processor import Processor, logger

class Convolution(Processor):
    def get_input_keys(self, data):
        return ["magpat", "source_fft"]

    def run(self, data):
        kernel_fft = data.get("source_fft")
        magpat = data["magpat"]
        if kernel_fft is None:
            return {"convolved_magpat": magpat}
        shape = magpat.shape
        if shape[0] & 1:
            logger.info("Correcting for an odd pixel height of the pattern")
            magpat = magpat[:-1]
        if shape[1] & 1:
            logger.info("Correcting for an odd pixel width of the pattern")
            magpat = magpat[:,:-1]
        convolved_pattern = numpy.empty_like(magpat)
        convolved_pattern[:] = numpy.fft.irfft2(
            numpy.fft.rfft2(magpat) * kernel_fft)
        if shape[0] & 1:
            convolved_pattern = numpy.vstack((convolved_pattern,
                                              convolved_pattern[-1:]))
        if shape[1] & 1:
            convolved_pattern = numpy.hstack((convolved_pattern,
                                              convolved_pattern[:,-1:]))
        convolved_pattern = numpy.ascontiguousarray(convolved_pattern)
        return {"convolved_magpat": convolved_pattern}

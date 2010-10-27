import pyfits
import numpy
from processor import Processor, logger

def write_fits(fits_output_file, magpat, lenses,
               region_x0, region_x1, region_y0, region_y1):
    img_hdu = pyfits.PrimaryHDU(magpat)
    for s in ["x0", "y0", "x1", "y1"]:
        img_hdu.header.update("magpat" + s, locals()["region_" + s])
    lenses = numpy.asarray(lenses)
    col_x = pyfits.Column(name="x", format="D", array=lenses[:,0])
    col_y = pyfits.Column(name="y", format="D", array=lenses[:,1])
    col_mass = pyfits.Column(name="mass", format="D", array=lenses[:,2])
    lens_hdu = pyfits.new_table([col_x, col_y, col_mass])
    lens_hdu.name = "lenses"
    pyfits.HDUList([img_hdu, lens_hdu]).writeto(open(fits_output_file, "w"))
    logger.info("Wrote magnification pattern to %s", fits_output_file)

def read_fits(fits_input_file):
    output = {}
    hdus = pyfits.open(fits_input_file)
    magpat =  numpy.ascontiguousarray(hdus[0].data, dtype=numpy.float32)
    output["magpat"] = magpat
    output["ypixels"], output["xpixels"] = magpat.shape
    for s in ["x0", "y0", "x1", "y1"]:
        if "magpat" + s in hdus[0].header:
            output["region_" + s] = hdus[0].header["magpat" + s]
    if len(hdus) > 1 and hdus[1].name.lower() == "lenses":
        lenses = hdus[1].data
        if lenses.dtype.names != ("x", "y", "mass"):
            lenses = numpy.hstack((lenses["x"], lenses["y"], lenses["mass"]))
        if not lenses.dtype.isnative:
            lenses = lenses.byteswap(True).newbyteorder()
        output["lenses"] = lenses
    logger.info("Read magnification pattern from %s", fits_input_file)
    return output

class FITSWriter(Processor):
    def get_input_keys(self, data):
        return ["fits_output_file", "magpat", "lenses",
                "region_x0", "region_x1", "region_y0", "region_y1"]

    def run(self, data):
        d = dict((key, data[key]) for key in self.get_input_keys(data))
        write_fits(**d)
        return {}

class FITSReader(Processor):
    def get_input_keys(self, data):
        return ["fits_input_file"]

    def run(self, data):
        return read_fits(data["fits_input_file"])

# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import pyfits
import numpy
import lensconfig
import magpat
import utils

def write_fits(magpat, fits_output_file):
    """Save a magnification pattern to a FITS file.

    The pattern itself is saved in the pimary HDU of the FITS file.
    The coordinates of the source plane rectangle occupied by the
    pattern are stored in the header fields

        MAGPATX0, MAGPATY0, MAGPATX1, MAGPATY1

    The lens list is stored in a binary table HDU named "LENSES".

    Parameters:

        magpat           magnification pattern to save
        fits_output_file
                         file name of the output file
    """
    img_hdu = pyfits.PrimaryHDU(magpat)
    for s in ["x0", "y0", "x1", "y1"]:
        img_hdu.header.update("magpat" + s, getattr(magpat.region, s))
    lens_hdu = pyfits.new_table(magpat.lenses)
    lens_hdu.name = "lenses"
    pyfits.HDUList([img_hdu, lens_hdu]).writeto(open(fits_output_file, "w"))
    utils.logger.info("Wrote magnification pattern to %s", fits_output_file)

def read_fits(fits_input_file):
    """Read a magnification pattern from a FITS file.

    The function returns a Magpat instance including the list of
    lenses read from the file.

    Parameters:

        fits_input_file  filename of the FITS file to read
    """
    hdus = pyfits.open(fits_input_file)
    buf = numpy.ascontiguousarray(hdus[0].data, dtype=numpy.float32)
    ypixels, xpixels = buf.shape
    region_params = {}
    for s in ["x0", "y0", "x1", "y1"]:
        region_params[s] = hdus[0].header.get("magpat" + s, float(s[1]))
    region = utils.rectangle(**region_params)
    if hdus[-1].name.lower() == "lenses":
        data = hdus[-1].data
        if data.dtype.names == ("x", "y", "mass") and data.dtype.isnative:
            lenses = lensconfig.LensConfig(data)
        else:
            lenses = lensconfig.LensConfig(num_lenses=len(data))
            lenses.x, lenses.y, lenses.mass = data.x, data.y, data.mass
    else:
        lenses = None
    utils.logger.info("Read magnification pattern from %s", fits_input_file)
    return magpat.Magpat(xpixels, ypixels, lenses, region, buf)

# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from __future__ import division, absolute_import
from astropy.io import fits
import numpy
from . import lensconfig
from . import magpat
from . import utils

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
    img_hdu = fits.PrimaryHDU(magpat)
    region = magpat.region
    img_hdu.header.update(ctype1=" ",
                          crpix1=0.5,
                          crval1=region.x,
                          cdelt1=region.width / magpat.params.xpixels,
                          ctype2=" ",
                          crpix2=0.5,
                          crval2=region.y,
                          cdelt2=region.height / magpat.params.ypixels)
    for s in ["x0", "y0", "x1", "y1"]:
        img_hdu.header.update([("magpat" + s, getattr(region, s))])
    lens_hdu = fits.BinTableHDU(magpat.lenses, name="lenses")
    fits.HDUList([img_hdu, lens_hdu]).writeto(fits_output_file, overwrite=True)
    utils.logger.info("Wrote magnification pattern to %s", fits_output_file)

def read_fits(fits_input_file):
    """Read a magnification pattern from a FITS file.

    The function returns a Magpat instance including the list of
    lenses read from the file.

    Parameters:

        fits_input_file  filename of the FITS file to read
    """
    hdus = fits.open(fits_input_file)
    buf = numpy.ascontiguousarray(hdus[0].data, dtype=numpy.float32)
    ypixels, xpixels = buf.shape
    region_params = {}
    for s in ["x0", "y0", "x1", "y1"]:
        region_params[s] = hdus[0].header.get("magpat" + s, float(s[1]))
    region = utils.rectangle(**region_params)
    if hdus[-1].name.lower() == "lenses":
        lenses = lensconfig.LensConfig.fromarray(hdus[-1].data)
    else:
        lenses = None
    utils.logger.info("Read magnification pattern from %s", fits_input_file)
    return magpat.Magpat(xpixels, ypixels, lenses, region, buf)

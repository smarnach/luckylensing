# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from luckylensing import logger
from PIL import Image

def save_img(magpat, imgfile, min_mag=None, max_mag=None):
    """Save a rendering of the magnification pattern to a file.

    The magnification pattern is rendered using the standard color
    palette and saved to a file using the Python Imaging Library.  The
    file format is derived from the file name extension.

    Parameters:

        magpat           the magnification pattern
        imgfile          file name (will be overwritten if existent)
        min_mag, max_mag
                         passed on to Magpat.render_gradient()
    """
    buf = magpat.render_gradient(min_mag=min_mag, max_mag=max_mag)
    Image.fromarray(buf).save(imgfile)
    logger.info("Wrote magnification pattern to %s", imgfile)

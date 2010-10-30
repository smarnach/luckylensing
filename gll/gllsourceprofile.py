# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import numpy
import gtk
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView
from luckylensing import SourceProfile

class GllSourceProfile(GllPlugin):
    name = "Source profile"

    def __init__(self):
        super(GllSourceProfile, self).__init__(SourceProfile())
        self.main_widget = GllImageView(self.get_pixbuf)
        self.config_widget = GllConfigBox()
        self.config_widget.add_radio_buttons(
            "profile_type", "Source profile type", "flat",
            [("Flat", "flat"), ("Gaussian", "gaussian")])
        self.config_widget.add_items(
             ("source_radius", "Source radius", (0.01, 0.0, 1e10, 0.001), 4))

    def update(self, data):
        self.source = data["source_profile"]
        self.main_widget.mark_dirty()

    def get_pixbuf(self):
        ypixels, xpixels = self.source.shape
        source = numpy.vstack((self.source[ypixels//2:], self.source[:ypixels//2]))
        source = numpy.hstack((source[:,xpixels//2:], source[:,:xpixels//2]))
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                xpixels, ypixels)
        array = numpy.rollaxis(pixbuf.get_pixels_array(), 2, 0)
        array[:] = source*(255/source.max())
        return pixbuf

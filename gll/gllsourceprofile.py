# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import numpy
import gtk
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox, GllConfigCheckButton
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
        show_profile = GllConfigCheckButton("Show profile")
        show_profile.set_active(True)
        self.config_widget.add_items(
            [("source_radius", "Source radius", (0.01, 0.0, 1e10, 0.001), 4),
             ("export_kernel", show_profile)])

    def update(self, data):
        self.show = data["export_kernel"]
        if self.show:
            self.source = data["source_profile"]
        self.main_widget.mark_dirty()

    def set_config(self, config):
        config.setdefault("export_kernel", True)
        GllPlugin.set_config(self, config)

    def get_pixbuf(self):
        if self.show:
            source = self.source
        else:
            source = numpy.ones((1, 1))
        ypixels, xpixels = source.shape
        source = numpy.vstack((source[ypixels//2:], source[:ypixels//2]))
        source = numpy.hstack((source[:,xpixels//2:], source[:,:xpixels//2]))
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                xpixels, ypixels)
        array = numpy.rollaxis(pixbuf.get_pixels_array(), 2, 0)
        array[:] = source*(255/source.max())
        return pixbuf

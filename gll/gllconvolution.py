# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import luckylensing as ll
from gllplugin import GllPlugin
from gllimageview import GllImageView
import gtk

class GllConvolution(GllPlugin):
    name = "Convolution"

    def __init__(self):
        super(GllConvolution, self).__init__(ll.convolve)
        self.main_widget = GllImageView(self.get_pixbuf)

    def update(self, data):
        magpat = data["magpat"]
        ypixels, xpixels = magpat.shape
        self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                     xpixels, ypixels)
        data["magpat_pixbuf"] = self.pixbuf
        self.buf = magpat.render_gradient(
            min_mag=data["min_mag"], max_mag=data["max_mag"],
            buf=self.pixbuf.get_pixels_array())
        self.main_widget.mark_dirty()

    def get_pixbuf(self):
        return self.pixbuf

# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import luckylensing as ll
from gllplugin import GllPlugin
from gllimageview import GllImageView
import gtk

colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
          (195, 16, 16), (249, 249, 70), (255, 255, 255)]
steps = [255, 32, 255, 255, 255]

class GllConvolution(GllPlugin):
    name = "Convolution"

    def __init__(self):
        super(GllConvolution, self).__init__(ll.Convolution())
        self.main_widget = GllImageView(self.get_pixbuf)

    def update(self, data):
        magpat = data["magpat"]
        ypixels, xpixels = magpat.shape
        self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                     xpixels, ypixels)
        data["magpat_pixbuf"] = self.pixbuf
        self.buf = ll.render_magpattern_gradient(
            magpat, colors, steps, data["min_mag"], data["max_mag"],
            self.pixbuf.get_pixels_array())
        self.main_widget.mark_dirty()

    def get_pixbuf(self):
        return self.pixbuf

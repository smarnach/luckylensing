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
        if self.source is None:
            return numpy.zeros((1, 1, 3), dtype=numpy.uint8)
        ypixels, xpixels = self.source.shape
        source = numpy.vstack((self.source[ypixels/2:], self.source[:ypixels/2]))
        source = numpy.hstack((source[:,xpixels/2:], source[:,:xpixels/2]))
        source = numpy.array(source*(255/source.max()), dtype=numpy.uint8)
        return source.reshape(source.shape + (1,)).repeat(3, axis=2)

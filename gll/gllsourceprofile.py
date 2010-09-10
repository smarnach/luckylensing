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
        self.radio_flat = gtk.RadioButton(None, "Flat")
        self.radio_gaussian = gtk.RadioButton(self.radio_flat, "Gaussian")
        radiobuttons = gtk.VBox()
        radiobuttons.pack_start(self.radio_flat)
        radiobuttons.pack_start(self.radio_gaussian)
        profile_chooser = gtk.HBox()
        profile_label = gtk.Label("Source profile type")
        profile_label.set_alignment(0.0, 0.0)
        profile_label.set_padding(0, 4)
        profile_chooser.pack_start(profile_label, False)
        profile_chooser.pack_start(radiobuttons)
        self.config_widget = GllConfigBox(
            [profile_chooser,
             ("source_radius", "Source radius", (0.01, 0.0, 1e10, 0.001), 4)])

    def get_config(self):
        config = self.config_widget.get_config()
        if self.radio_flat.get_active():
            config["profile_type"] = "flat"
        elif self.radio_gaussian.get_active():
            config["profile_type"] = "gaussian"
        return config

    def set_config(self, config):
        self.config_widget.set_config(config)
        if config["profile_type"] == "flat":
            self.radio_flat.set_active(True)
        elif config["profile_type"] == "gaussian":
            self.radio_gaussian.set_active(True)

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

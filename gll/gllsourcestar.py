import numpy
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView
from sourcestar import FlatSource, GaussianSource

class GllSourceStar(GllPlugin):
    def __init__(self, processor):
        super(GllSourceStar, self).__init__(processor)
        self.main_widget = GllImageView(self.get_pixbuf)
        self.config_widget = GllConfigBox(
            [("source_radius", "Source radius", (0.01, 0.0, 1e10, 0.001), 4)])

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

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

class GllFlatSource(GllSourceStar):
    def __init__(self):
        super(GllFlatSource, self).__init__(FlatSource())

class GllGaussianSource(GllSourceStar):
    def __init__(self):
        super(GllGaussianSource, self).__init__(GaussianSource())

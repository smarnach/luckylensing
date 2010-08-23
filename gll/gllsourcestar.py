import gtk
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from sourcestar import FlatSource, GaussianSource

class GllFlatSource(GllPlugin):
    def __init__(self):
        super(GllFlatSource, self).__init__(FlatSource())
        self.config_widget = GllConfigBox(
            [("source_radius", "Source radius", (0.01, 0.0, 1e10, 0.001), 4)])

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

class GllGaussianSource(GllPlugin):
    def __init__(self):
        super(GllGaussianSource, self).__init__(GaussianSource())
        self.config_widget = GllConfigBox(
            [("source_radius", "Source radius", (0.01, 0.0, 1e10, 0.001), 4)])

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

import gtk
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from globularcluster import GlobularCluster

class GllGlobularCluster(GllPlugin):
    name = "Globular cluster"

    def __init__(self):
        super(GllGlobularCluster, self).__init__(GlobularCluster())
        self.config_widget = GllConfigBox(
            [("num_stars", "Number of stars", (1000, 0, 100000, 1), 0),
             ("random_seed", "Random seed", (42, -1000000, 1000000, 1), 0),
             ("log_mass", "Log of mean mass", (-7.0, -50.0, 50.0, 0.1), 2),
             ("log_mass_stddev", "Log(mass) std dev", (0.1, 0.0, 50.0, 0.1), 2),
             ("angle", "Rotation angle", (0.0, -100.0, 100.0, 0.01), 4),
             ("region_radius", "Region radius", (1.0, 0.0, 1000.0, 0.1), 2)])

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

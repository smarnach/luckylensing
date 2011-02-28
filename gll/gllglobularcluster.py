# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
import luckylensing as ll

class GllGlobularCluster(GllPlugin):
    name = "Globular cluster"

    def __init__(self):
        super(GllGlobularCluster, self).__init__(ll.globular_cluster)
        self.config_widget = GllConfigBox(
            [("num_stars", "Number of stars", (1000, 0, 100000, 1), 0),
             ("random_seed", "Random seed", (42, -1000000, 1000000, 1), 0),
             ("total_mass", "Total mass", (1.0, 0.0, 1e10, 0.05), 2),
             ("log_mass_stddev", "Log(mass) std dev", (0.0, 0.0, 10.0, 0.05), 2),
             ("angle", "Rotation angle", (0.0, -100.0, 100.0, 0.01), 4),
             ("region_radius", "Region radius", (1.0, 0.0, 1000.0, 0.1), 2)])

    def get_config(self):
        config = self.config_widget.get_config()
        config["region"] = dict(radius=config["region_radius"])
        return config

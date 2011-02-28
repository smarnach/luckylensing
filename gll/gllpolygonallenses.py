# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
import luckylensing as ll

class GllPolygonalLenses(GllPlugin):
    name = "Polygonal lens configuration"

    def __init__(self):
        super(GllPolygonalLenses, self).__init__(ll.polygonal_lenses)
        self.config_widget = GllConfigBox(
            [("num_stars", "Number of stars", (5, 0, 1000, 1), 0),
             ("total_mass", "Total mass", (1.0, 0.0, 1e10, 0.05), 2),
             ("angle", "Rotation angle", (0.0, -100.0, 100.0, 0.01), 4),
             ("region_radius", "Region radius", (1.5, 0.0, 1000.0, 0.1), 2)])
        self.config_widget.declare_record("region")

# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import gtk
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
import luckylensing as ll
import numpy

class GllLensConfig(GllPlugin):
    def __init__(self, action=None):
        GllPlugin.__init__(self, action)
        self.lenses = []
        self.region = None
        self.main_widget = gtk.DrawingArea()
        self.main_widget.set_size_request(400, 300)
        self.main_widget.connect("expose-event", self.draw)
        self.main_widget.show()

    def update(self, data):
        self.lenses = data["lenses"]
        if not isinstance(self.lenses, ll.LensConfig):
            self.lenses = ll.LensConfig(self.lenses)
        self.region = data.get("region")
        if self.region is not None:
            self.region = ll.rectangle(**self.region)

    def draw(self, area, event):
        if not len(self.lenses):
            return
        pix_width, pix_height = area.window.get_size()
        cr = area.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y,
                      event.area.width, event.area.height)
        cr.clip()

        # Render background
        cr.set_source_color(area.style.black)
        cr.paint()

        # Transform to lens plane coordinates
        sqrt_mass = numpy.sqrt(self.lenses.mass)
        x0 = (self.lenses.x - sqrt_mass).min()
        y0 = (self.lenses.y - sqrt_mass).min()
        width = (self.lenses.x + sqrt_mass).max() - x0
        height = (self.lenses.y + sqrt_mass).max() - y0
        x0 -= width * 0.05
        y0 -= height * 0.05
        width *= 1.1
        height *= 1.1
        scale = min(pix_width / width, pix_height / height)
        xshift = (pix_width - scale * width) / 2
        yshift = (pix_height - scale * height) / 2
        cr.translate(xshift, pix_height - yshift)
        cr.scale(scale, -scale)
        cr.translate(-x0, -y0)

        # Render the lenses
        cr.set_line_width(0.5 / scale)
        min_radius = 0.7 / scale
        for lens in self.lenses:
            x, y, radius = lens.x, lens.y, numpy.sqrt(lens.mass)
            cr.arc(x, y, radius, 0, 2.0 * numpy.pi)
            cr.set_source_rgba(0.5, 0.3, 1.0, 0.1)
            cr.fill_preserve()
            cr.set_source_rgba(0.5, 0.3, 1.0, 0.9)
            cr.stroke()
            cr.arc(x, y, max(0.01 * radius, min_radius), 0, 2.0 * numpy.pi)
            cr.set_source_rgba(1.0, 0.8, 0.2, 1.0)
            cr.fill()

        # Render the rectangle corresponding to the magnification pattern
        if self.region is not None:
            cr.rectangle(*self.region)
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            cr.stroke()

class GllLenses(GllLensConfig):
    name = "Lens configuration"

    def __init__(self):
        GllLensConfig.__init__(self)
        self.builder = gtk.Builder()
        self.builder.add_from_file("glllenses.glade")
        self.builder.connect_signals(self)
        self.lens_list = self.builder.get_object("lens_list")
        self.lens_selection = self.builder.get_object("treeview").get_selection()
        self.lens_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.config_widget = GllConfigBox()
        self.config_widget.add_toggle_group(
            "export_region", "Magnification pattern region", True,
            [("region_x0", "Left coordinate",  (-1.0, -1e10, 1e10, 0.01), 4),
             ("region_y0", "Lower coordinate", (-1.0, -1e10, 1e10, 0.01), 4),
             ("region_x1", "Right coordinate", ( 1.0, -1e10, 1e10, 0.01), 4),
             ("region_y1", "Upper coordinate", ( 1.0, -1e10, 1e10, 0.01), 4)])
        self.config_widget.add(self.builder.get_object("lens_box"))
        self.config_widget.declare_record("region", "export_region")

    def get_config(self):
        config = self.config_widget.get_config()
        all_lenses = map(tuple, self.lens_list)
        config["all_lenses"] = all_lenses
        config["lenses"] = [lens[1:] for lens in all_lenses if lens[0]]
        return config

    def set_config(self, config):
        self.config_widget.set_config(config)
        all_lenses = config.get("all_lenses")
        if all_lenses is not None:
            self.lens_list.clear()
            for lens in all_lenses:
                self.lens_list.append(lens)

    def toggle_lens(self, cell, path):
        self.lens_list[path][0] ^= True
    def edit_lens_cell1(self, cell, path, new_text):
        self.lens_list[path][1] = float(new_text)
    def edit_lens_cell2(self, cell, path, new_text):
        self.lens_list[path][2] = float(new_text)
    def edit_lens_cell3(self, cell, path, new_text):
        self.lens_list[path][3] = float(new_text)
    def add_lens(self, button):
        self.lens_list.append((True, 0.0, 0.0, 0.0))
    def delete_lens(self, button):
        lens_list, selected = self.lens_selection.get_selected_rows()
        for row_path in reversed(selected):
            lens_list.remove(lens_list.get_iter(row_path))

class GllGlobularCluster(GllLensConfig):
    name = "Globular cluster"

    def __init__(self):
        GllLensConfig.__init__(self, ll.globular_cluster)
        self.config_widget = GllConfigBox(
            [("num_stars", "Number of stars", (1000, 0, 100000, 1), 0),
             ("random_seed", "Random seed", (42, -1000000, 1000000, 1), 0),
             ("total_mass", "Total mass", (1.0, 0.0, 1e10, 0.05), 2),
             ("log_mass_stddev", "Log(mass) std dev", (0.0, 0.0, 10.0, 0.05), 2),
             ("angle", "Rotation angle", (0.0, -100.0, 100.0, 0.01), 4),
             ("region_radius", "Region radius", (1.0, 0.0, 1000.0, 0.1), 2)])
        self.config_widget.declare_record("region")

class GllPolygonalLenses(GllLensConfig):
    name = "Polygonal lens configuration"

    def __init__(self):
        GllLensConfig.__init__(self, ll.polygonal_lenses)
        self.config_widget = GllConfigBox(
            [("num_stars", "Number of stars", (5, 0, 1000, 1), 0),
             ("total_mass", "Total mass", (1.0, 0.0, 1e10, 0.05), 2),
             ("angle", "Rotation angle", (0.0, -100.0, 100.0, 0.01), 4),
             ("region_radius", "Region radius", (1.5, 0.0, 1000.0, 0.1), 2)])
        self.config_widget.declare_record("region")

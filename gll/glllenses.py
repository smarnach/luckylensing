# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import gtk
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox

class GllLenses(GllPlugin):
    name = "Lens configuration"

    def __init__(self):
        super(GllLenses, self).__init__()
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

import sys
sys.path.append("../libll")

import gtk
import luckylensing as ll
from gllplugin import GllPlugin

class GllLenses(GllPlugin):
    def __init__(self):
        super(GllLenses, self).__init__()
        self.name = "Lenses"
        self.builder = gtk.Builder()
        self.builder.add_from_file("glllenses.glade")
        self.builder.connect_signals(self)
        self.lens_list = self.builder.get_object("lens_list")
        self.lens_selection = self.builder.get_object("treeview").get_selection()
        self.lens_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.config_widget = self.builder.get_object("frame")

    def get_config(self):
        d = {}
        all_lenses = map(tuple, self.lens_list)
        d["all_lenses"] = all_lenses
        d["lenses"] = [lens[1:] for lens in all_lenses if lens[0]]
        return d

    def set_config(self, config):
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

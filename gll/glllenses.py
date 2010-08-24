import gtk
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
        self.config_widget = self.builder.get_object("config")
        self.set_config({"export_region": True,
                         "region_x0": -1.,
                         "region_y0": -1.,
                         "region_x1":  1.,
                         "region_y1":  1.})

    def get_config(self):
        d = {}
        exp_reg = self.builder.get_object("export_region").get_active()
        d["export_region"] = exp_reg
        if exp_reg:
            for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
                d[key] = self.builder.get_object(key).get_value()
        all_lenses = map(tuple, self.lens_list)
        d["all_lenses"] = all_lenses
        d["lenses"] = [lens[1:] for lens in all_lenses if lens[0]]
        return d

    def set_config(self, config):
        exp_reg = config["export_region"]
        self.builder.get_object("export_region").set_active(exp_reg)
        self.toggle_export_region()
        if exp_reg:
            for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
                self.builder.get_object(key).set_value(config[key])
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

    def toggle_export_region(self, *args):
        state = self.builder.get_object("export_region").get_active()
        for name in ["x0", "x1", "y0", "y1"]:
            self.builder.get_object("label_" + name).set_sensitive(state)
            self.builder.get_object("spinbutton_" + name).set_sensitive(state)

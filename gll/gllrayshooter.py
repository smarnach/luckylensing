import sys
sys.path.append("../libll")

import gtk
import gtkimageview
import luckylensing as ll
from rayshooter import Rayshooter
from gllplugin import GllPlugin

class GllRayshooter(GllPlugin):
    def __init__(self):
        super(GllRayshooter, self).__init__()
        self.imageview = gtkimageview.ImageView()
        self.imageview.set_interpolation(gtk.gdk.INTERP_TILES)
        self.scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        self.scrollwin.show_all()
        self.dragger = self.imageview.get_tool()
        self.selector = gtkimageview.ImageToolSelector(self.imageview)
        self.imageview.connect("button-press-event", self.imageview_clicked)
        self.builder = gtk.Builder()
        self.builder.add_from_file("gllrayshooter.glade")
        self.builder.connect_signals(self)
        self.lens_list = self.builder.get_object("lens_list")
        self.lens_selection = self.builder.get_object("treeview").get_selection()
        self.lens_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.set_config({"xpixels": 1024,
                         "ypixels": 1024,
                         "region_x0": -.1,
                         "region_y0": -.3,
                         "region_x1":  .5,
                         "region_y1":  .3,
                         "density": 100,
                         "kernel": ll.KERNEL_TRIANGULATED})
        self.processor = Rayshooter()
        self.main_widget = self.scrollwin
        self.config_widget = self.builder.get_object("config")

    def get_config(self):
        d = {"num_threads": 2}
        self.imageview.grab_focus()
        all_lenses = map(tuple, self.lens_list)
        d["all_lenses"] = all_lenses
        d["lenses"] = ll.Lenses([lens[1:] for lens in all_lenses if lens[0]])
        d["xpixels"] = int(self.builder.get_object("xpixels").get_value())
        d["ypixels"] = int(self.builder.get_object("ypixels").get_value())
        if self.imageview.get_tool() is self.selector:
            rect = self.selector.get_selection()
            width = max(rect.width, rect.height*d["xpixels"]/d["ypixels"])
            x = rect.x + (rect.width - width)/2
            xfactor = self.region.width/d["xpixels"]
            d["region_x0"] = self.region.x + x * xfactor
            d["region_x1"] = d["region_x0"] + width * xfactor
            height = max(rect.height, rect.width*d["ypixels"]/d["xpixels"])
            y = rect.y + (rect.height - height)/2
            yfactor = self.region.height/d["ypixels"]
            d["region_y0"] = self.region.y + y * yfactor
            d["region_y1"] =d["region_y0"]  + height * yfactor
        else:
            for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
                d[key] = self.builder.get_object(key).get_value()
        d["density"] = self.builder.get_object("density").get_value()
        if self.builder.get_object("kernel_simple").get_active():
            d["kernel"] = ll.KERNEL_SIMPLE
        elif self.builder.get_object("kernel_bilinear").get_active():
            d["kernel"] = ll.KERNEL_BILINEAR
        elif self.builder.get_object("kernel_triangulated").get_active():
            d["kernel"] = ll.KERNEL_TRIANGULATED
        return d

    def set_config(self, config):
        all_lenses = config.get("all_lenses")
        if all_lenses is not None:
            self.lens_list.clear()
            for lens in all_lenses:
                self.lens_list.append(lens)
        self.builder.get_object("xpixels").set_value(config["xpixels"])
        self.builder.get_object("ypixels").set_value(config["ypixels"])
        for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
            self.builder.get_object(key).set_value(config[key])
        self.builder.get_object("density").set_value(config["density"])
        if config["kernel"] == ll.KERNEL_SIMPLE:
            self.builder.get_object("kernel_simple").set_active(True)
        elif config["kernel"] == ll.KERNEL_BILINEAR:
            self.builder.get_object("kernel_bilinear").set_active(True)
        elif config["kernel"] == ll.KERNEL_TRIANGULATED:
            self.builder.get_object("kernel_triangulated").set_active(True)

    def update(self, data):
        colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
                  (195, 16, 16), (249, 249, 70), (255, 255, 255)]
        steps = [255, 32, 255, 255, 255]
        buf = ll.render_magpattern_gradient(data["magpat"], colors, steps)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf,
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        self.imageview.set_tool(self.dragger)
        self.imageview.set_pixbuf(self.pixbuf)
        for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
            self.builder.get_object(key).set_value(data[key])
        self.region = ll.Rect(data["region_x0"], data["region_y0"],
                              data["region_x1"] - data["region_x0"],
                              data["region_y1"] - data["region_y0"])

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

    def imageview_clicked(self, widget, event, data=None):
        widget.grab_focus()
        if event.button == 1:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self.emit("run-pipeline")
        if event.button == 3:
            if widget.get_tool() is self.dragger:
                widget.set_tool(self.selector)
            else:
                widget.set_tool(self.dragger)

import sys
sys.path.append("../libll")

import gtk
import gtkimageview
import luckylensing as ll
from rayshooter import Rayshooter
from gllplugin import GllPlugin

class GllRayshooter(GllPlugin):
    def __init__(self):
        super(GllRayshooter, self).__init__(Rayshooter())
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
        self.set_config({"xpixels": 1024,
                         "ypixels": 1024,
                         "density": 100,
                         "num_threads": 2,
                         "kernel": ll.KERNEL_TRIANGULATED,
                         "export_region": False,
                         "region_x0": -1.,
                         "region_y0": -1.,
                         "region_x1":  1.,
                         "region_y1":  1.})
        self.region = None
        self.xpixels = None
        self.ypixels = None
        self.main_widget = self.scrollwin
        self.config_widget = self.builder.get_object("config")

    def get_config(self):
        d = {}
        self.imageview.grab_focus()
        d["xpixels"] = int(self.builder.get_object("xpixels").get_value())
        d["ypixels"] = int(self.builder.get_object("ypixels").get_value())
        exp_reg = self.builder.get_object("export_region").get_active()
        d["export_region"] = exp_reg
        if self.region and self.imageview.get_tool() is self.selector:
            rect = self.selector.get_selection()
            width = max(rect.width, rect.height*self.xpixels/self.ypixels)
            x = rect.x + (rect.width - width)/2
            xfactor = (self.region["x1"]-self.region["x0"])/self.xpixels
            d["region_x0"] = self.region["x0"] + x * xfactor
            d["region_x1"] = d["region_x0"] + width * xfactor
            height = max(rect.height, rect.width*self.ypixels/self.xpixels)
            y = rect.y + (rect.height - height)/2
            yfactor = (self.region["y1"]-self.region["y0"])/self.ypixels
            d["region_y1"] = self.region["y1"] - y * yfactor
            d["region_y0"] = d["region_y1"] - height * yfactor
        else:
            if exp_reg:
                for key in ["region_x0", "region_x1",
                            "region_y0", "region_y1"]:
                    d[key] = self.builder.get_object(key).get_value()
        d["density"] = self.builder.get_object("density").get_value()
        d["num_threads"] = int(self.builder.get_object("num_threads"
                                                       ).get_value())
        if self.builder.get_object("kernel_simple").get_active():
            d["kernel"] = ll.KERNEL_SIMPLE
        elif self.builder.get_object("kernel_bilinear").get_active():
            d["kernel"] = ll.KERNEL_BILINEAR
        elif self.builder.get_object("kernel_triangulated").get_active():
            d["kernel"] = ll.KERNEL_TRIANGULATED
        return d

    def set_config(self, config):
        self.builder.get_object("xpixels").set_value(config["xpixels"])
        self.builder.get_object("ypixels").set_value(config["ypixels"])
        exp_reg = config["export_region"]
        self.builder.get_object("export_region").set_active(exp_reg)
        self.toggle_export_region()
        for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
            if key in config:
                self.builder.get_object(key).set_value(config[key])
        self.builder.get_object("density").set_value(config["density"])
        self.builder.get_object("num_threads").set_value(config["num_threads"])
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
        self.region = {}
        for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
            self.builder.get_object(key).set_value(data[key])
            self.region[key[7:]] = data[key]
        self.xpixels = data["xpixels"]
        self.ypixels = data["ypixels"]

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

    def toggle_export_region(self, *args):
        state = self.builder.get_object("export_region").get_active()
        for name in ["x0", "x1", "y0", "y1"]:
            self.builder.get_object("label_" + name).set_sensitive(state)
            self.builder.get_object("spinbutton_" + name).set_sensitive(state)

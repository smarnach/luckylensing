import gtk
import gtkimageview
import luckylensing as ll
from rayshooter import Rayshooter
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView

class GllRayshooter(GllPlugin):
    name = "Magnification pattern"

    def __init__(self):
        super(GllRayshooter, self).__init__(Rayshooter())
        self.main_widget = GllImageView(self.get_pixbuf)
        self.imageview = self.main_widget.imageview
        self.imageview.connect("button-press-event", self.imageview_clicked)
        self.dragger = self.imageview.get_tool()
        self.selector = gtkimageview.ImageToolSelector(self.imageview)
        self.radio_simple = gtk.RadioButton(None, "Simple")
        self.radio_bilinear = gtk.RadioButton(self.radio_simple, "Bilinear")
        self.radio_triangulated = gtk.RadioButton(self.radio_simple,
                                                  "Triangulated")
        radiobuttons = gtk.VBox()
        radiobuttons.pack_start(self.radio_simple)
        radiobuttons.pack_start(self.radio_bilinear)
        radiobuttons.pack_start(self.radio_triangulated)
        kernel_chooser = gtk.HBox()
        kernel_label = gtk.Label("Ray shooting kernel")
        kernel_label.set_alignment(0.0, 0.0)
        kernel_label.set_padding(0, 4)
        kernel_chooser.pack_start(kernel_label, False)
        kernel_chooser.pack_start(radiobuttons)
        self.config_widget = GllConfigBox(
            [("xpixels", "Resolution x", (1024, 0, 16384, 16), 0),
             ("ypixels", "Resolution y", (1024, 0, 16384, 16), 0),
             ("density", "Ray density", (100.0, 0.0, 100000.0, 1.0), 1),
             ("num_threads", "Number of threads", (2, 0, 32, 1), 0),
             kernel_chooser])
        self.radio_bilinear.set_active(True)
        self.config_widget.add_toggle_block(
            "export_region", "Ray shooting region", False,
            [("region_x0", "Left coordinate",  (-1.0, -1e10, 1e10, 0.01), 4),
             ("region_y0", "Lower coordinate", (-1.0, -1e10, 1e10, 0.01), 4),
             ("region_x1", "Right coordinate", ( 1.0, -1e10, 1e10, 0.01), 4),
             ("region_y1", "Upper coordinate", ( 1.0, -1e10, 1e10, 0.01), 4)])
        self.region = None
        self.xpixels = None
        self.ypixels = None

    def get_config(self):
        config = self.config_widget.get_config()
        if self.region and self.imageview.get_tool() is self.selector:
            rect = self.selector.get_selection()
            width = max(rect.width, rect.height*self.xpixels/self.ypixels)
            x = rect.x + (rect.width - width)/2
            xfactor = (self.region["x1"]-self.region["x0"])/self.xpixels
            config["region_x0"] = self.region["x0"] + x * xfactor
            config["region_x1"] = config["region_x0"] + width * xfactor
            height = max(rect.height, rect.width*self.ypixels/self.xpixels)
            y = rect.y + (rect.height - height)/2
            yfactor = (self.region["y1"]-self.region["y0"])/self.ypixels
            config["region_y1"] = self.region["y1"] - y * yfactor
            config["region_y0"] = config["region_y1"] - height * yfactor
        if self.radio_simple.get_active():
            config["kernel"] = ll.KERNEL_SIMPLE
        elif self.radio_bilinear.get_active():
            config["kernel"] = ll.KERNEL_BILINEAR
        elif self.radio_triangulated.get_active():
            config["kernel"] = ll.KERNEL_TRIANGULATED
        return config

    def set_config(self, config):
        self.config_widget.set_config(config)
        if config["kernel"] == ll.KERNEL_SIMPLE:
            self.radio_simple.set_active(True)
        elif config["kernel"] == ll.KERNEL_BILINEAR:
            self.radio_bilinear.set_active(True)
        elif config["kernel"] == ll.KERNEL_TRIANGULATED:
            self.radio_triangulated.set_active(True)

    def update(self, data):
        colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
                  (195, 16, 16), (249, 249, 70), (255, 255, 255)]
        steps = [255, 32, 255, 255, 255]
        self.buf = ll.render_magpattern_gradient(data["magpat"], colors, steps)
        self.imageview.set_tool(self.dragger)
        self.main_widget.mark_dirty()
        data["magpat_pic"] = self.buf
        self.region = {}
        for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
            self.config_widget.set_value(key, data[key])
            self.region[key[7:]] = data[key]
        self.xpixels = data["xpixels"]
        self.ypixels = data["ypixels"]

    def get_pixbuf(self):
        return self.buf

    def imageview_clicked(self, widget, event, data=None):
        if event.button == 1:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self.emit("run-pipeline")
        if event.button == 3:
            if widget.get_tool() is self.dragger:
                widget.set_tool(self.selector)
                self.config_widget.set_active("export_region", True)
            else:
                widget.set_tool(self.dragger)

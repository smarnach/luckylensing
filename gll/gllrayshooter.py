from math import log10
import gtk
import gtkimageview
import luckylensing as ll
from rayshooter import Rayshooter
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView

colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
          (195, 16, 16), (249, 249, 70), (255, 255, 255)]
steps = [255, 32, 255, 255, 255]

class GllRayshooter(GllPlugin):
    name = "Magnification pattern"

    def __init__(self):
        super(GllRayshooter, self).__init__(Rayshooter())
        self.main_widget = GllImageView(self.get_pixbuf)
        self.imageview = self.main_widget.imageview
        self.imageview.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                                  gtk.gdk.POINTER_MOTION_MASK |
                                  gtk.gdk.LEAVE_NOTIFY_MASK)
        self.imageview.connect("button-press-event", self.imageview_clicked)
        self.imageview.connect("motion-notify-event", self.imageview_motion)
        self.imageview.connect("leave-notify-event", self.imageview_leave)
        self.main_widget.connect("parent-set", self.imageview_leave)
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
            "export_region", "Magnification pattern region", False,
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
            config["region_x0"] = self.region["x0"] + x * self.xfactor
            config["region_x1"] = config["region_x0"] + width * self.xfactor
            height = max(rect.height, rect.width*self.ypixels/self.xpixels)
            y = rect.y + (rect.height - height)/2
            config["region_y1"] = self.region["y1"] - y * self.yfactor
            config["region_y0"] = config["region_y1"] - height * self.yfactor
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
        self.magpat = data["magpat"]
        self.buf = ll.render_magpattern_gradient(self.magpat, colors, steps)
        self.imageview.set_tool(self.dragger)
        self.main_widget.mark_dirty()
        data["magpat_pic"] = self.buf
        self.region = {}
        for key in ["region_x0", "region_x1", "region_y0", "region_y1"]:
            self.config_widget.set_value(key, data[key])
            self.region[key[7:]] = data[key]
        self.xpixels = data["xpixels"]
        self.ypixels = data["ypixels"]
        self.xfactor = (self.region["x1"]-self.region["x0"])/self.xpixels
        self.yfactor = (self.region["y1"]-self.region["y0"])/self.ypixels
        xlog = log10(abs(self.region["x0"]) + abs(self.region["x1"]))
        if -2.0 <= xlog < 0.0:
            xprec = int(-log10(self.xfactor) + 1)
        else:
            xprec = int(xlog - log10(self.xfactor) + 1)
        if xlog < -2.0:
            self.xformat = "%" + (".%ie" % xprec)
        else:
            self.xformat = "%" + (".%if" % xprec)
        ylog = log10(abs(self.region["y0"]) + abs(self.region["y1"]))
        if -2.0 <= ylog < 0.0:
            yprec = int(-log10(self.yfactor) + 1)
        else:
            yprec = int(ylog - log10(self.yfactor) + 1)
        if ylog < -2.0:
            self.yformat = "%" + (".%ie" % yprec)
        else:
            self.yformat = "%" + (".%if" % yprec)

    def get_pixbuf(self):
        return self.buf

    def imageview_clicked(self, imageview, event):
        if event.button == 1:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self.emit("run-pipeline")
        if event.button == 3:
            if imageview.get_tool() is self.dragger:
                imageview.set_tool(self.selector)
                self.config_widget.set_active("export_region", True)
            else:
                imageview.set_tool(self.dragger)

    def imageview_motion(self, imageview, event):
        draw_rect = self.imageview.get_draw_rect()
        if self.region is None or draw_rect is None:
            return
        zoom = self.imageview.get_zoom()
        viewport = self.imageview.get_viewport()
        mag_x = (event.x - draw_rect.x + viewport.x) / zoom
        mag_y = self.ypixels - (event.y - draw_rect.y + viewport.y + 1) / zoom
        if (mag_x < 0 or mag_x >= self.xpixels or
            mag_y < 0 or mag_y >= self.ypixels):
            self.emit("statusbar-pop")
            return
        x = self.region["x0"] + mag_x * self.xfactor
        y = self.region["y0"] + mag_y * self.yfactor
        mag = self.magpat[mag_y][mag_x]
        text = (("x: " + self.xformat + ", y: " + self.yformat +
                 ", magnification: %.2f") % (x, y, mag))
        self.emit("statusbar-push", text)

    def imageview_leave(self, imageview, event):
        self.emit("statusbar-pop")

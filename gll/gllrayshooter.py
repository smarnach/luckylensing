# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from math import log10
import gtk
import gtkimageview
import luckylensing as ll
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView
from gllutils import save_dialog

class GllRayshooter(GllPlugin):
    name = "Magnification pattern"

    def __init__(self):
        super(GllRayshooter, self).__init__(ll.Rayshooter)
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
        self.config_widget = GllConfigBox(
            [("xpixels", "Resolution x", (1024, 0, 16384, 16), 0),
             ("ypixels", "Resolution y", (1024, 0, 16384, 16), 0),
             ("density", "Ray density", (100.0, 0.0, 100000.0, 1.0), 1),
             ("num_threads", "Number of threads", (2, 0, 32, 1), 0)])
        self.config_widget.add_radio_buttons(
            "kernel", "Ray shooting kernel", "triangulated",
            [("Simple", "simple"),
             ("Bilinear", "bilinear"),
             ("Triangulated", "triangulated")])
        self.config_widget.add_toggle_group(
            "export_region", "Magnification pattern region", False,
            [("region_x0", "Left coordinate",  (-1.0, -1e10, 1e10, 0.01), 4),
             ("region_y0", "Lower coordinate", (-1.0, -1e10, 1e10, 0.01), 4),
             ("region_x1", "Right coordinate", ( 1.0, -1e10, 1e10, 0.01), 4),
             ("region_y1", "Upper coordinate", ( 1.0, -1e10, 1e10, 0.01), 4)])
        self.config_widget.declare_record("region", "export_region")
        self.magpat = None
        self.region = None

    def get_config(self):
        config = self.config_widget.get_config()
        if self.region is not None and self.imageview.get_tool() is self.selector:
            rect = self.selector.get_selection()
            width = max(rect.width, rect.height*self.xpixels//self.ypixels)
            x = rect.x + (rect.width - width)//2
            x0 = self.region.x0 + x * self.xfactor
            height = max(rect.height, rect.width*self.ypixels//self.xpixels)
            y = rect.y + (rect.height - height)//2
            y0 = self.region.y1 - y * self.yfactor - height * self.yfactor
            config["region"] = dict(x0=x0, y0=y0,
                                    x1=x0 + width * self.xfactor,
                                    y1=y0 + height * self.yfactor)
        return config

    def update(self, data):
        self.magpat = data["magpat"]
        data["min_mag"] = self.magpat.min()
        data["max_mag"] = self.magpat.max()
        self.ypixels, self.xpixels = self.magpat.shape
        self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                     self.xpixels, self.ypixels)
        data["magpat_pixbuf"] = self.pixbuf
        self.magpat.render_gradient(buf=self.pixbuf.get_pixels_array())
        self.imageview.set_tool(self.dragger)
        self.main_widget.mark_dirty()
        self.region = self.magpat.region
        self.xfactor = self.region.width / self.xpixels
        self.yfactor = self.region.height / self.ypixels
        xlog = log10(abs(self.region.x0) + abs(self.region.x1))
        if -2.0 <= xlog < 0.0:
            xprec = int(-log10(self.xfactor) + 1)
        else:
            xprec = int(xlog - log10(self.xfactor) + 1)
        if xlog < -2.0:
            self.xformat = "%" + (".%ie" % xprec)
        else:
            self.xformat = "%" + (".%if" % xprec)
        ylog = log10(abs(self.region.y0) + abs(self.region.y1))
        if -2.0 <= ylog < 0.0:
            yprec = int(-log10(self.yfactor) + 1)
        else:
            yprec = int(ylog - log10(self.yfactor) + 1)
        if ylog < -2.0:
            self.yformat = "%" + (".%ie" % yprec)
        else:
            self.yformat = "%" + (".%if" % yprec)

    def get_pixbuf(self):
        return self.pixbuf

    def imageview_clicked(self, imageview, event):
        if event.button == 1:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self.emit("run-pipeline")
        if event.button == 3:
            if imageview.get_tool() is self.dragger:
                imageview.set_tool(self.selector)
                self.config_widget["export_region"].set_active(True)
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
        x = self.region.x0 + mag_x * self.xfactor
        y = self.region.y0 + mag_y * self.yfactor
        mag = self.magpat[mag_y][mag_x]
        text = (("x: " + self.xformat + ", y: " + self.yformat +
                 ", magnification: %.2f") % (x, y, mag))
        self.emit("statusbar-push", text)

    def imageview_leave(self, imageview, event):
        self.emit("statusbar-pop")

    def save_png(self, *args):
        filename = save_dialog("Save Magnification Pattern Image",
                               [("PNG Image Files", "*.png")])
        if filename is not None:
            self.pixbuf.save(filename, "png")

    def save_fits(self, *args):
        filename = save_dialog("Save Magnification Pattern",
                               [("FITS Image Files", "*.fits")])
        if filename is not None:
            self.magpat.write_fits(filename)

    def get_actions(self):
        save_sensitive = hasattr(self, "pixbuf")
        return [("Save FITS", self.save_fits, save_sensitive),
                ("Save PNG", self.save_png, save_sensitive)]

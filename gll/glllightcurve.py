import gtk
import gtkimageview
from lightcurve import LightCurve
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox

class GllLightCurve(GllPlugin):
    def __init__(self):
        super(GllLightCurve, self).__init__(LightCurve())
        self.imageview = gtkimageview.ImageView()
        self.imageview.set_interpolation(gtk.gdk.INTERP_TILES)
        self.imageview.connect("button-press-event", self.imageview_clicked)
        scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        scrollwin.show_all()
        self.main_widget = scrollwin
        self.export_max = gtk.CheckButton("Set upper magnification")
        self.export_max.connect("toggled", self.toggle_export_max)
        self.config_widget = GllConfigBox(
            [self.export_max,
             ("curve_max_mag", "Upper magnification", (10.0, 0.0, 1e10, 1.0), 1)])
        self.toggle_export_max()

    def get_config(self):
        d = {}
        export_max = self.export_max.get_active()
        d["export_max"] = export_max
        if export_max:
            d.update(self.config_widget.get_config())
        return d

    def set_config(self, config):
        export_max = config["export_max"]
        self.export_max.set_active(export_max)
        if export_max:
            self.config_widget.set_config(config)

    def update(self, data):
        xpixels = data["xpixels"]
        ypixels = data["ypixels"]
        curve = data["light_curve"]
        samples = len(curve)
        max_mag = data.get("curve_max_mag", curve.max())
        points = [(int(i*(xpixels-1)/(samples-1)),
                   int((ypixels-1)*(1.0-mag/max_mag)))
                  for i, mag in enumerate(curve) if mag]
        pixmap = gtk.gdk.Pixmap(None, xpixels, ypixels, 24)
        gc = self.imageview.style.bg_gc[gtk.STATE_NORMAL]
        pixmap.draw_rectangle(gc, True, 0, 0, xpixels, ypixels)
        gc = self.imageview.style.fg_gc[gtk.STATE_NORMAL]
        pixmap.draw_lines(gc, points)
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False,
                                8, xpixels, ypixels)
        pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(),
                                 0, 0, 0, 0, xpixels, ypixels)
        self.imageview.set_pixbuf(pixbuf)

    def imageview_clicked(self, widget, event, data=None):
        widget.grab_focus()

    def toggle_export_max(self, *args):
        state = self.export_max.get_active()
        self.config_widget[1].set_sensitive(state)

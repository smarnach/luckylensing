import gtk
from lightcurve import LightCurve
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView

class GllLightCurve(GllPlugin):
    name = "Light curve"

    def __init__(self):
        super(GllLightCurve, self).__init__(LightCurve())
        self.main_widget = GllImageView(self.get_pixbuf)
        self.config_widget = GllConfigBox()
        self.config_widget.add_toggle_block(
            "export_max", "Set upper magnification", False,
            [("curve_max_mag", "Upper magnification", (10.0, 0.0, 1e10, 1.0), 1)])

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

    def update(self, data):
        self.xpixels = data["xpixels"]
        self.ypixels = data["ypixels"]
        curve = data["light_curve"]
        samples = len(curve)
        max_mag = data.get("curve_max_mag", curve.max()*1.2)
        self.points = [(int(i*(self.xpixels-1)/(samples-1)),
                        int((self.ypixels-1)*(1.0-mag/max_mag)))
                       for i, mag in enumerate(curve) if mag]
        self.main_widget.mark_dirty()

    def get_pixbuf(self):
        pixmap = gtk.gdk.Pixmap(None, self.xpixels, self.ypixels, 24)
        gc = self.main_widget.style.bg_gc[gtk.STATE_NORMAL]
        pixmap.draw_rectangle(gc, True, 0, 0, self.xpixels, self.ypixels)
        gc = self.main_widget.style.fg_gc[gtk.STATE_NORMAL]
        pixmap.draw_lines(gc, self.points)
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False,
                                8, self.xpixels, self.ypixels)
        pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(),
                                 0, 0, 0, 0, self.xpixels, self.ypixels)
        return pixbuf

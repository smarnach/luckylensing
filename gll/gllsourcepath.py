import gtk
from lightcurve import LightCurve
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView

class GllSourcePath(GllPlugin):
    def __init__(self):
        super(GllSourcePath, self).__init__()
        self.name = "SourcePath"
        self.main_widget = GllImageView(self.get_pixbuf)
        self.config_widget = GllConfigBox(
            [("curve_x0", "Start x coordinate", (0.35, -1e10, 1e10, 0.01), 4),
             ("curve_y0", "Start y coordinate", (-0.025, -1e10, 1e10, 0.01), 4),
             ("curve_x1", "End x coordinate", (0.4, -1e10, 1e10, 0.01), 4),
             ("curve_y1", "End y coordinate", (0.02, -1e10, 1e10, 0.01), 4),
             ("curve_samples", "Number of samples", (256, 0, 1000000, 16), 0)])

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

    def update(self, data):
        self.xpixels = data["xpixels"]
        self.ypixels = data["ypixels"]
        region_x0 = data["region_x0"]
        region_y0 = data["region_y0"]
        region_x1 = data["region_x1"]
        region_y1 = data["region_y1"]
        pixels_per_width = self.xpixels / (region_x1 - region_x0)
        pixels_per_height = self.ypixels / (region_y1 - region_y0)
        self.coords = (int((data["curve_x0"] - region_x0) * pixels_per_width),
                       int((region_y1 - data["curve_y0"]) * pixels_per_height),
                       int((data["curve_x1"] - region_x0) * pixels_per_width),
                       int((region_y1 - data["curve_y1"]) * pixels_per_height))
        self.magpat_buf = data["magpat_pic"]
        self.main_widget.mark_dirty()

    def get_pixbuf(self):
        magpat_pixbuf = gtk.gdk.pixbuf_new_from_array(
            self.magpat_buf, gtk.gdk.COLORSPACE_RGB, 8)
        pixmap = gtk.gdk.Pixmap(None, self.xpixels, self.ypixels, 24)
        gc = self.main_widget.style.light_gc[gtk.STATE_NORMAL]
        pixmap.draw_pixbuf(gc, magpat_pixbuf, 0, 0, 0, 0)
        pixmap.draw_line(gc, *self.coords)
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False,
                                8, self.xpixels, self.ypixels)
        pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(),
                                 0, 0, 0, 0, self.xpixels, self.ypixels)
        return pixbuf

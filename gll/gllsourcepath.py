import gtk
import gtkimageview
from lightcurve import LightCurve
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox

class GllSourcePath(GllPlugin):
    def __init__(self):
        super(GllSourcePath, self).__init__()
        self.name = "SourcePath"
        self.imageview = gtkimageview.ImageView()
        self.imageview.set_interpolation(gtk.gdk.INTERP_TILES)
        self.imageview.connect("button-press-event", self.imageview_clicked)
        scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        scrollwin.show_all()
        self.main_widget = scrollwin
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
        xpixels = data["xpixels"]
        ypixels = data["ypixels"]
        region_x0 = data["region_x0"]
        region_y0 = data["region_y0"]
        region_x1 = data["region_x1"]
        region_y1 = data["region_y1"]
        pixels_per_width = xpixels / (region_x1 - region_x0)
        pixels_per_height = ypixels / (region_y1 - region_y0)
        x0 = int((data["curve_x0"] - region_x0) * pixels_per_width)
        y0 = int((region_y1 - data["curve_y0"]) * pixels_per_height)
        x1 = int((data["curve_x1"] - region_x0) * pixels_per_width)
        y1 = int((region_y1 - data["curve_y1"]) * pixels_per_height)
        pixmap = gtk.gdk.Pixmap(None, xpixels, ypixels, 24)
        gc = self.imageview.style.light_gc[gtk.STATE_NORMAL]
        pixmap.draw_pixbuf(gc, data["magpat_pixbuf"], 0, 0, 0, 0)
        pixmap.draw_line(gc, x0, y0, x1, y1)
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False,
                                8, xpixels, ypixels)
        pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(),
                                 0, 0, 0, 0, xpixels, ypixels)
        self.imageview.set_pixbuf(pixbuf)

    def imageview_clicked(self, widget, event, data=None):
        widget.grab_focus()

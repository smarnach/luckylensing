from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox
from gllimageview import GllImageView
import gtk
import gtkimageview
import gobject
from gllutils import save_dialog

class ImageToolSourcePath(gobject.GObject, gtkimageview.IImageTool):
    def __init__(self):
        gobject.GObject.__init__(self)
        self.crosshair = gtk.gdk.Cursor(gtk.gdk.CROSSHAIR)
        self.cache = gtkimageview.PixbufDrawCache()

    def do_button_press(self, event):
        pass

    def do_button_release(self, event):
        pass

    def do_motion_notify(self, event):
        pass

    def do_pixbuf_changed(self, reset_fit, rect):
        pass

    def do_paint_image(self, opts, drawable):
        self.cache.draw(opts, drawable)
        x0 = self.coords[0] * opts.zoom - opts.zoom_rect.x + opts.widget_x
        y0 = self.coords[1] * opts.zoom - opts.zoom_rect.y + opts.widget_y
        x1 = self.coords[2] * opts.zoom - opts.zoom_rect.x + opts.widget_x
        y1 = self.coords[3] * opts.zoom - opts.zoom_rect.y + opts.widget_y
        ctx = drawable.cairo_create()
        ctx.rectangle(opts.widget_x, opts.widget_y,
                      opts.zoom_rect.width, opts.zoom_rect.height)
        ctx.clip()
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        ctx.stroke()

    def do_cursor_at_point(self, x, y):
        return self.crosshair

gobject.type_register(ImageToolSourcePath)

class GllSourcePath(GllPlugin):
    name = "Source path"

    def __init__(self):
        super(GllSourcePath, self).__init__()
        self.main_widget = GllImageView(self.get_pixbuf)
        self.tool = ImageToolSourcePath()
        self.main_widget.imageview.set_tool(self.tool)
        self.config_widget = GllConfigBox(
            [("curve_x0", "Start x coordinate", (-1.0, -1e10, 1e10, 0.01), 4),
             ("curve_y0", "Start y coordinate", (0.0, -1e10, 1e10, 0.01), 4),
             ("curve_x1", "End x coordinate", (1.0, -1e10, 1e10, 0.01), 4),
             ("curve_y1", "End y coordinate", (0.0, -1e10, 1e10, 0.01), 4),
             ("curve_samples", "Number of samples", (256, 0, 1000000, 16), 0)])
        for key in ["curve_x0", "curve_y0", "curve_x1", "curve_y1"]:
            self.config_widget.adjustments[key].connect(
                "value_changed", self.coords_changed)

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

    def update(self, data):
        try:
            self.xpixels = data["xpixels"]
            self.ypixels = data["ypixels"]
            self.region_x0 = data["region_x0"]
            self.region_y0 = data["region_y0"]
            self.region_x1 = data["region_x1"]
            self.region_y1 = data["region_y1"]
            self.magpat_buf = data["magpat_pic"]
        except KeyError:
            return
        self.update_coords(data)

    def update_coords(self, data):
        pixels_per_width = self.xpixels / (self.region_x1 - self.region_x0)
        pixels_per_height = self.ypixels / (self.region_y1 - self.region_y0)
        self.tool.coords = (
            (data["curve_x0"] - self.region_x0) * pixels_per_width,
            (self.region_y1 - data["curve_y0"]) * pixels_per_height,
            (data["curve_x1"] - self.region_x0) * pixels_per_width,
            (self.region_y1 - data["curve_y1"]) * pixels_per_height)
        self.main_widget.mark_dirty()

    def get_pixbuf(self):
        return self.magpat_buf

    def coords_changed(self, *args):
        if hasattr(self, "magpat_buf"):
            self.update_coords(self.config_widget.get_config())

    def save_png(self, *args):
        filename = save_dialog("Save Magnification Pattern Image",
                               [("PNG Image Files", "*.png")])
        if filename is None:
            return
        magpat_pixbuf = gtk.gdk.pixbuf_new_from_array(
            self.magpat_buf, gtk.gdk.COLORSPACE_RGB, 8)
        pixmap = gtk.gdk.Pixmap(None, self.xpixels, self.ypixels, 24)
        cr = pixmap.cairo_create()
        cr.set_source_pixbuf(magpat_pixbuf, 0, 0)
        cr.paint()
        cr.move_to(*self.tool.coords[:2])
        cr.line_to(*self.tool.coords[2:])
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.stroke()
        cr.get_target().write_to_png(filename)

    def get_actions(self):
        if hasattr(self, "magpat_buf"):
            return [("Save PNG", self.save_png)]
        return []

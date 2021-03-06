# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

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
            self.config_widget[key].adjustment.connect(
                "value_changed", self.coords_changed)

    def update(self, data):
        try:
            self.xpixels = data["xpixels"]
            self.ypixels = data["ypixels"]
            self.region = data["magpat"].region
            self.pixbuf = data["magpat_pixbuf"]
        except KeyError:
            return
        self.update_coords(data)

    def update_coords(self, data):
        pixels_per_width = self.xpixels / self.region.width
        pixels_per_height = self.ypixels / self.region.height
        self.tool.coords = (
            (data["curve_x0"] - self.region.x0) * pixels_per_width,
            (self.region.y1 - data["curve_y0"]) * pixels_per_height,
            (data["curve_x1"] - self.region.x0) * pixels_per_width,
            (self.region.y1 - data["curve_y1"]) * pixels_per_height)
        self.main_widget.mark_dirty()

    def get_pixbuf(self):
        return self.pixbuf

    def coords_changed(self, *args):
        if hasattr(self, "pixbuf"):
            self.update_coords(self.config_widget.get_config())

    def save_png(self, *args):
        filename = save_dialog("Save Magnification Pattern Image",
                               [("PNG Image Files", "*.png")])
        if filename is None:
            return
        pixmap = gtk.gdk.Pixmap(None, self.xpixels, self.ypixels, 24)
        cr = pixmap.cairo_create()
        cr.set_source_pixbuf(self.pixbuf, 0, 0)
        cr.paint()
        cr.move_to(*self.tool.coords[:2])
        cr.line_to(*self.tool.coords[2:])
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.stroke()
        cr.get_target().write_to_png(filename)

    def get_actions(self):
        return [("Save PNG", self.save_png, hasattr(self, "pixbuf"))]

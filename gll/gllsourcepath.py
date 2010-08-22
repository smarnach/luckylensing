import gtk
from lightcurve import LightCurve
from gllplugin import GllPlugin

class GllSourcePath(GllPlugin):
    def __init__(self):
        super(GllSourcePath, self).__init__()
        self.name = "SourcePath"
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.connect("expose-event", self.expose)
        self.main_widget = gtk.Alignment(0.5, 0.5)
        self.main_widget.add(self.drawing_area)
        self.main_widget.show_all()
        self.points = None
        self.pixbuf = None

    def get_config(self):
        return {"curve_x0": .35, "curve_y0": -.025,
                "curve_x1": .4, "curve_y1":  .02}

    def update(self, data):
        xpixels = data["xpixels"]
        ypixels = data["ypixels"]
        region_x0 = data["region_x0"]
        region_y0 = data["region_y0"]
        region_x1 = data["region_x1"]
        region_y1 = data["region_y1"]
        pixels_per_width = xpixels / (region_x1 - region_x0)
        pixels_per_height = ypixels / (region_y1 - region_y0)
        x0 = (data["curve_x0"] - region_x0) * pixels_per_width
        y0 = (region_y1 - data["curve_y0"]) * pixels_per_height
        x1 = (data["curve_x1"] - region_x0) * pixels_per_width 
        y1 = (region_y1 - data["curve_y1"]) * pixels_per_height
        self.points = map(int, [x0, y0, x1, y1])
        self.pixbuf = data["magpat_pixbuf"]
        self.drawing_area.set_size_request(xpixels, ypixels)
        self.drawing_area.queue_draw_area(0, 0, xpixels, ypixels)

    def expose(self, area, event):
        if self.pixbuf:
            drawable = area.window
            gc = area.style.light_gc[gtk.STATE_NORMAL]
            drawable.draw_pixbuf(gc, self.pixbuf, 0, 0, 0, 0)
            if self.points:
                drawable.draw_line(gc, *self.points)

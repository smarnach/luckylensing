import gtk
from lightcurve import LightCurve
from gllplugin import GllPlugin

class GllLightCurve(GllPlugin):
    def __init__(self):
        super(GllLightCurve, self).__init__(LightCurve())
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.connect("expose-event", self.expose)
        self.main_widget = gtk.Alignment(0.5, 0.5)
        self.main_widget.add(self.drawing_area)
        self.main_widget.show_all()
        self.points = None

    def get_config(self):
        return {"curve_max_mag": 10.0}

    def update(self, data):
        xpixels = data["xpixels"]
        ypixels = data["ypixels"]
        curve = data["light_curve"]
        samples = len(curve)
        max_mag = data.get("curve_max_mag", curve.max())
        self.points = [(int(i*(xpixels-1)/(samples-1)),
                        int((ypixels-1)*(1.0-mag/max_mag)))
                       for i, mag in enumerate(curve)]
        self.drawing_area.set_size_request(xpixels, ypixels)
        self.drawing_area.queue_draw_area(0, 0, xpixels, ypixels)

    def expose(self, area, event):
        if self.points:
            drawable = area.window
            gc = drawable.new_gc()
            drawable.draw_lines(gc, self.points)

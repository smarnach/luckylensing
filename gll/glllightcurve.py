import gtk
from lightcurve import LightCurve
from gllplugin import GllPlugin
from gllconfigbox import GllConfigBox

class GllLightCurve(GllPlugin):
    name = "Light curve"

    def __init__(self):
        super(GllLightCurve, self).__init__(LightCurve())
        self.main_widget = gtk.DrawingArea()
        self.main_widget.set_size_request(400, 300)
        self.main_widget.show()
        self.main_widget.connect("expose-event", self.draw)
        self.config_widget = GllConfigBox()
        self.config_widget.add_toggle_block(
            "export_max", "Set upper magnification", False,
            [("curve_max_mag", "Upper magnification", (10.0, 0.0, 1e10, 1.0), 1)])

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

    def update(self, data):
        curve = data["light_curve"]
        self.max_mag = data.get("curve_max_mag", curve.max()*1.1)
        self.num_samples = len(curve)
        self.points = [(i, mag) for i, mag in enumerate(curve) if mag]

    def draw(self, area, event):
        if not len(self.points):
            return
        cr = area.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y,
                      event.area.width, event.area.height)
        cr.clip()
        matrix = cr.get_matrix()
        width, height = area.window.get_size()
        cr.translate(0.1 * width, 0.9 * height)
        cr.scale(0.8*width / (self.num_samples-1), -0.8*height / self.max_mag)
        cr.rectangle(0.0, 0.0, self.num_samples-1, self.max_mag)
        cr.clip_preserve()
        cr.move_to(*self.points[0])
        for p in self.points[1:]:
            cr.line_to(*p)
        cr.set_matrix(matrix)
        cr.stroke()

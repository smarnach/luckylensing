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
        self.points = []

    def get_config(self):
        return self.config_widget.get_config()

    def set_config(self, config):
        self.config_widget.set_config(config)

    def update(self, data):
        curve = data["light_curve"]
        self.max_mag = data.get("curve_max_mag")
        disp_max = self.max_mag
        if self.max_mag is None:
            disp_max = curve.max() * 1.01
        factor = 1.0
        while True:
            if disp_max <= 1.2:
                disp_max = 2 * round(0.5*disp_max + 0.05, 1)
                step = 0.2
                break
            if disp_max <= 3.0:
                disp_max = 5 * round(0.2*disp_max + 0.05, 1)
                step = 0.5
                break
            if disp_max <= 6.0:
                disp_max = round(disp_max + 0.5, 0)
                step = 1.0
                break
            factor *= 10.0
            disp_max /= 10.0
        if self.max_mag is None:
            self.max_mag = factor * disp_max
        self.grid_step = factor * step
        self.grid_lines = int(round(self.max_mag/self.grid_step, 10)) + 1
        self.num_samples = len(curve)
        self.points = [(i, mag) for i, mag in enumerate(curve) if mag]

    def draw(self, area, event):
        if not len(self.points):
            return
        width, height = area.window.get_size()
        cr = area.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y,
                      event.area.width, event.area.height)
        cr.clip()
        pixel_mat = cr.get_matrix()

        # Transform to graph coordinates
        cr.translate(0.1 * width, 0.9 * height)
        cr.scale(0.8*width / (self.num_samples-1), -0.8*height / self.max_mag)
        graph_mat = cr.get_matrix()

        # Render background and frame
        cr.rectangle(0.0, 0.0, self.num_samples-1, self.max_mag)
        rect = cr.copy_path()
        cr.set_source_color(area.style.white)
        cr.fill_preserve()
        cr.set_matrix(pixel_mat)
        cr.set_source_color(area.style.black)
        cr.set_line_width(0.5)
        cr.stroke()

        # render the grid lines
        cr.set_matrix(graph_mat)
        for i in range(1, self.grid_lines):
            y = i * self.grid_step
            cr.move_to(0, y)
            cr.line_to(self.num_samples-1, y)
        cr.set_matrix(pixel_mat)
        cr.set_line_width(0.25)
        cr.stroke()

        # Render the axis marks
        cr.set_font_size(12.0)
        cr.set_source_color(area.style.text[area.state])
        pix_x = 0.1*width - 5.0
        for i in range(self.grid_lines):
            y = i * self.grid_step
            text = "%#.2g" % y
            xbear, ybear, w, h, xadv, yadv = cr.text_extents(text)
            pix_y = (0.9 - 0.8*y / self.max_mag) * height
            cr.move_to(pix_x - w - xbear, pix_y - h/2.0 - ybear)
            cr.show_text(text)

        # Render the curve
        cr.set_matrix(graph_mat)
        cr.append_path(rect)
        cr.clip()
        cr.move_to(*self.points[0])
        for p in self.points[1:]:
            cr.line_to(*p)
        cr.set_matrix(pixel_mat)
        cr.set_source_rgb(0.75, 0.0, 0.0)
        cr.set_line_width(2.0)
        cr.stroke()

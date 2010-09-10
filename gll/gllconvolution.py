import luckylensing as ll
from gllplugin import GllPlugin
from gllimageview import GllImageView

colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
          (195, 16, 16), (249, 249, 70), (255, 255, 255)]
steps = [255, 32, 255, 255, 255]

class GllConvolution(GllPlugin):
    name = "Convolution"

    def __init__(self):
        super(GllConvolution, self).__init__(ll.Convolution())
        self.main_widget = GllImageView(self.get_pixbuf)

    def update(self, data):
        magpat = data["magpat"]
        convolved_magpat = data["convolved_magpat"]
        min_mag = magpat.min()
        max_mag = magpat.max()
        self.buf = ll.render_magpattern_gradient(
            convolved_magpat, colors, steps, min_mag, max_mag)
        self.main_widget.mark_dirty()
        data["min_mag"] = min_mag
        data["max_mag"] = max_mag
        data["convolved_magpat_pic"] = self.buf

    def get_pixbuf(self):
        return self.buf

import gtk
import gtkimageview
import luckylensing as ll
from convolution import Convolution
from gllplugin import GllPlugin

class GllConvolution(GllPlugin):
    def __init__(self):
        super(GllConvolution, self).__init__(Convolution())
        self.imageview = gtkimageview.ImageView()
        scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        scrollwin.show_all()
        self.main_widget = scrollwin

    def update(self, data):
        colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
                  (195, 16, 16), (249, 249, 70), (255, 255, 255)]
        steps = [255, 32, 255, 255, 255]
        magpat = data["magpat"]
        convolved_magpat = data["convolved_magpat"]
        min_mag = magpat.min()
        max_mag = magpat.max()
        buf = ll.render_magpattern_gradient(convolved_magpat, colors, steps,
                                            min_mag, max_mag)
        pixbuf = gtk.gdk.pixbuf_new_from_array(buf, gtk.gdk.COLORSPACE_RGB, 8)
        self.imageview.set_pixbuf(pixbuf)
        data["min_mag"] = min_mag
        data["max_mag"] = max_mag
        data["convolved_magpat_pixbuf"] = pixbuf

from math import sqrt, log
from time import clock
import gobject
import gtk
import gtkimageview
import numpy
import luckylens as ll

class MagPattern(ll.Rayshooter):
    def __init__(self, params):
        super(MagPattern, self).__init__(params, 3)
        self.density = 100
        self.count = None

    def start(self):
        assert self.params is not None

        params = self.params[0]
        self.count = numpy.zeros((params.ypixels, params.xpixels), numpy.int)

        # Determine shooting rectangle
        lens = [params.lenses.lens[i] for i in range(params.lenses.num_lenses)]
        rect = ll.Rect()
        x0 = min(l.x - sqrt(l.mass) for l in lens)
        d = sum(l.mass/(x0 - l.x) for l in lens)
        rect.x0 = min(x0, params.region.x0 + d)
        x1 = max(l.x + sqrt(l.mass) for l in lens)
        d = sum(l.mass/(x1 - l.x) for l in lens)
        rect.x1 = max(x1, params.region.x1 + d)
        y0 = min(l.y - sqrt(l.mass) for l in lens)
        d = sum(l.mass/(y0 - l.y) for l in lens)
        rect.y0 = min(y0, params.region.y0 + d)
        y1 = max(l.y + sqrt(l.mass) for l in lens)
        d = sum(l.mass/(y1 - l.y) for l in lens)
        rect.y1 = max(y1, params.region.y1 + d)

        # Determine number of rays needed to achieve the ray density
        # specified by self.density (assuming magnification = 1)
        rays = sqrt(self.density) / self.refine_final
        xrays = rays * params.xpixels
        yrays = rays * params.ypixels
        levels = max(0, int(log(min(xrays, yrays))/log(self.refine)))
        xrays /= self.refine**levels
        yrays /= self.refine**levels
        xrays *= (rect.x1 - rect.x0) / (params.region.x1 - params.region.x0)
        yrays *= (rect.y1 - rect.y0) / (params.region.y1 - params.region.y0)
        xrays = int(round(xrays))
        yrays = int(round(yrays))
        self.levels = levels + 2

        print xrays, yrays
        print self.levels

        t = clock()
        super(MagPattern, self).start(self.count, rect, xrays, yrays)
        print clock()-t

    def get_output(self, name):
        if name == "count":
            return self.count
        return None

class GllMagPattern(MagPattern):
    def __init__(self, params):
        super(GllMagPattern, self).__init__(params)
        self.imageview = gtkimageview.ImageView()
        self.scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        self.scrollwin.show_all()
        self.running = False

    def is_running(self):
        return self.running

    def main_widget(self):
        return self.scrollwin

    def start(self):
        self.running = True
        super(GllMagPattern, self).start()
        if self.cancel_flag:
            return
        buf = numpy.empty(self.count.shape + (1,), numpy.uint8)
        ll.image_from_magpat(buf, self.count)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf.repeat(3, axis=2),
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        gobject.idle_add(self.imageview.set_pixbuf, self.pixbuf)
        self.running = False

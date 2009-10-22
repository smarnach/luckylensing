#!/usr/bin/env python
import gtk
import numpy
import luckylens as ll
from time import clock

xpixels = 1024
ypixels = 512

class GllApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("gll.glade")
        self.builder.connect_signals(self)
        self.imgbuf = None
        self.m = 0

    def generate_pattern(self, *args):
        lens = (ll.Lens*3)((0.0, 0.0,  1.),
                           (1.2, 0.0,  2e-2),
                           (1.2, 0.025, 4e-3))
        lenses = ll.Lenses(3, lens)
        region = ll.Rect(.26, -.05, .46, .05)
        count = numpy.zeros((xpixels, ypixels), numpy.int)
        magpat = ll.new_MagPattern(lenses, region, xpixels, ypixels, 0, 0, count)
        rect = ll.Rect(-1., -.25, 1.5, .25)
        ll.rayshoot(magpat, rect, 1000, 200, 2)
        buf = numpy.zeros((xpixels, ypixels), numpy.uint8)
        ll.image_from_magpat(buf, magpat)
        box = self.builder.get_object("magpat_box")
        imgmap = gtk.gdk.Pixmap(box.window, xpixels, ypixels)
        imgmap.draw_gray_image(box.get_style().fg_gc[gtk.STATE_NORMAL],
                               0, 0, xpixels, ypixels, gtk.gdk.RGB_DITHER_NONE, buf)
        self.imgbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, xpixels, ypixels)
        self.imgbuf.get_from_drawable(imgmap, imgmap.get_colormap(), 0, 0, 0, 0, xpixels, ypixels)
        box.queue_resize()

    def show_pattern(self, widget, *args):
        if self.imgbuf is None:
            return
        x, y, width, height = widget.get_allocation()
        if width >= xpixels and height >= ypixels:
            m = xpixels*ypixels
        else:
            m = min(width * ypixels, height * xpixels)
        if m == self.m:
            return
        self.m = m
        imgscaled = self.imgbuf.scale_simple(m//ypixels, m//xpixels, gtk.gdk.INTERP_BILINEAR)
        self.builder.get_object("magpat").set_from_pixbuf(imgscaled)

    def app_quit(self, *args):
        gtk.main_quit()

app = GllApp()
gtk.main()

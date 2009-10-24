#!/usr/bin/env python
import gtk
import numpy
import luckylens as ll
import pyconsole
import threading
import gobject

xpixels = 1024
ypixels = 512

class RayshootThread(threading.Thread):
    def __init__(self, magpat, app):
        super(RayshootThread, self).__init__()
        self.magpat = magpat
        self.app = app

    def update_img(self, buf):
        self.box.remove(self.progress_box)
        self.box.add(self.img)
        imgmap = gtk.gdk.Pixmap(self.box.window, xpixels, ypixels)
        imgmap.draw_gray_image(self.box.get_style().fg_gc[gtk.STATE_NORMAL],
                               0, 0, xpixels, ypixels, gtk.gdk.RGB_DITHER_NONE, buf)
        self.app.imgbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, xpixels, ypixels)
        self.app.imgbuf.get_from_drawable(imgmap, imgmap.get_colormap(), 0, 0, 0, 0, xpixels, ypixels)
        self.box.queue_resize()
        self.app.m = 0

    def update_progressbar(self, fraction):
        self.bar.set_fraction(fraction)

    def init_progressbar(self):
        self.bar = self.app.builder.get_object("progressbar")
        self.box = self.app.builder.get_object("magpat_box")
        self.img = self.app.builder.get_object("magpat")
        self.progress_box = self.app.builder.get_object("progress_box")
        self.box.remove(self.img)
        self.box.add(self.progress_box)

    def run(self):
        gobject.idle_add(self.init_progressbar)
        fraction = 0.0
        for y in range(5):
            for x in range(25):
                rect = ll.Rect(-1. + x*.1, -.25+y*.1, -.9 + x*.1, -.15+y*.1)
                ll.rayshoot(self.magpat, rect, 20, 20, 2)
                fraction += 0.008
                gobject.idle_add(self.update_progressbar, min(fraction, 1.0))
        buf = numpy.zeros((xpixels, ypixels), numpy.uint8)
        ll.image_from_magpat(buf, self.magpat)
        gobject.idle_add(self.update_img, buf)

class GllApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("gll.glade")
        self.builder.connect_signals(self)
        self.imgbuf = None
        self.m = 0
        self.lens_list = self.builder.get_object("lens_list")

    def generate_pattern(self, *args):
        lens = (ll.Lens*3)(*map(tuple, self.lens_list))
        lenses = ll.Lenses(3, lens)
        region = ll.Rect(.26, -.05, .46, .05)
        self.count = numpy.zeros((xpixels, ypixels), numpy.int)
        magpat = ll.new_MagPattern(lenses, region, xpixels, ypixels, 0, 0, self.count)
        RayshootThread(magpat, self).start()

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

    def show_console(self, *args):
        window = gtk.Window()
        window.set_title("Gll Python Console")
        swin = gtk.ScrolledWindow()
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        window.add(swin)
        console = pyconsole.Console(locals=globals())
        swin.add(console)
        window.set_default_size(500, 400)
        window.show_all()

    def edit_lens_cell0(self, cell, path, new_text):
        self.lens_list[path][0] = float(new_text)
        return
    def edit_lens_cell1(self, cell, path, new_text):
        self.lens_list[path][1] = float(new_text)
        return
    def edit_lens_cell2(self, cell, path, new_text):
        self.lens_list[path][2] = float(new_text)
        return

    def quit_app(self, *args):
        gtk.main_quit()

gobject.threads_init()
app = GllApp()
gtk.main()

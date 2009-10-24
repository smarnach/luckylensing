#!/usr/bin/env python
import gtk
import numpy
import luckylens as ll
import pyconsole
import threading
import gobject
from time import sleep

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

    def update_progressbar(self):
        self.bar.set_fraction(min((self.progress1.value + self.progress1.value)*0.5, 1.0))

    def init_progressbar(self):
        self.bar = self.app.builder.get_object("progressbar")
        self.box = self.app.builder.get_object("magpat_box")
        self.img = self.app.builder.get_object("magpat")
        self.progress_box = self.app.builder.get_object("progress_box")
        self.box.remove(self.img)
        self.box.add(self.progress_box)

    def run(self):
        gobject.idle_add(self.init_progressbar)
        rect = ll.Rect(-1., -.25, 1.5, 0.)
        self.progress1 = ll.Progress();
        t1 = threading.Thread(target=ll.rayshoot, args=(self.magpat, rect, 100, 10, 3, self.progress1))
        t1.start()
        rect = ll.Rect(-1., 0., 1.5, .25)
        self.progress2 = ll.Progress();
        t2 = threading.Thread(target=ll.rayshoot, args=(self.magpat, rect, 100, 10, 3, self.progress2))
        t2.start()
        while t1.isAlive() or t2.isAlive():
            sleep(.05)
            gobject.idle_add(self.update_progressbar)
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

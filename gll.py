#!/usr/bin/env python
import gobject
import threading
import gtk
import pyconsole
import numpy
import luckylens as ll
from time import time

xpixels = 1024
ypixels = 512

class RayshootThread(threading.Thread):
    def __init__(self, params, magpat, callback):
        super(RayshootThread, self).__init__()
        self.magpat = magpat
        self.rs = ll.Rayshooter(params)
        self.callback = callback

    def progress(self):
        return self.rs.get_progress()

    def run(self):
        t = time()
        rect = ll.Rect(-1., -.25, 1.5, 0.)
        t1 = threading.Thread(target=self.rs.start,
                              args=(self.magpat, rect, 300, 30, 2))
        t1.start()
        rect = ll.Rect(-1., 0., 1.5, .25)
        t2 = threading.Thread(target=self.rs.start,
                              args=(self.magpat, rect, 300, 30, 2))
        t2.start()
        t1.join()
        t2.join()
        print time()-t
        buf = numpy.empty((ypixels, xpixels), numpy.uint8)
        ll.image_from_magpat(buf, self.magpat)
        gobject.idle_add(self.callback, buf)

class ConvolveThread(threading.Thread):
    def __init__(self, magpat, callback):
        super(ConvolveThread, self).__init__()
        self.magpat = magpat
        self.callback = callback

    def run(self):
        kernel = numpy.indices((ypixels/2, xpixels/2))
        kernel = numpy.exp(-sum(kernel*kernel)/8.)
        kernel = numpy.concatenate((kernel, numpy.flipud(kernel)), 0)
        kernel = numpy.concatenate((kernel, numpy.fliplr(kernel)), 1)
        kernel /= numpy.sum(kernel)
        self.magpat[:] = numpy.fft.irfft2(
            numpy.fft.rfft2(self.magpat) * numpy.fft.rfft2(kernel))
        buf = numpy.empty((ypixels, xpixels), numpy.uint8)
        ll.image_from_magpat(buf, self.magpat)
        gobject.idle_add(self.callback, buf)

class GllApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("gll.glade")
        self.builder.connect_signals(self)
        self.imgbuf = None
        self.magpat = numpy.empty((ypixels, xpixels), numpy.int)
        self.m = 0
        self.progressbar_active = False
        self.lens_list = self.builder.get_object("lens_list")
        self.magpat_box = self.builder.get_object("magpat_box")
        self.progressbar = self.builder.get_object("progressbar")
        self.magpat_img = self.builder.get_object("magpat")
        self.progress_box = self.builder.get_object("progress_box")

    def generate_pattern(self, *args):
        self.params = ll.MagPatternParams(self.lens_list, (.26, -.05, .46, .05),
                                          xpixels, ypixels)
        self.magpat[:] = 0;
        t = RayshootThread(self.params, self.magpat, self.update_img)
        self.init_progressbar()
        gobject.timeout_add(100, self.update_progressbar, t.progress)
        t.start()

    def convolve_pattern(self, *args):
        ConvolveThread(self.magpat, self.update_img).start()

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

    def update_img(self, buf):
        if self.progressbar_active:
            self.progressbar_active = False
            self.magpat_box.remove(self.progress_box)
            self.magpat_box.add(self.magpat_img)
        imgmap = gtk.gdk.Pixmap(self.magpat_box.window, xpixels, ypixels)
        imgmap.draw_gray_image(self.magpat_box.get_style().fg_gc[gtk.STATE_NORMAL],
                               0, 0, xpixels, ypixels, gtk.gdk.RGB_DITHER_NONE, buf)
        self.imgbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, xpixels, ypixels)
        self.imgbuf.get_from_drawable(imgmap, imgmap.get_colormap(), 0, 0, 0, 0, xpixels, ypixels)
        self.magpat_box.queue_resize()
        self.m = 0

    def update_progressbar(self, fraction):
        self.progressbar.set_fraction(min(fraction(), 1.0))
        return self.progressbar_active

    def init_progressbar(self):
        self.magpat_box.remove(self.magpat_img)
        self.magpat_box.add(self.progress_box)
        self.progressbar_active = True

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

    quit_app=gtk.main_quit

gobject.threads_init()
app = GllApp()
gtk.main()

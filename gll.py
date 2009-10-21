#!/usr/bin/env python
import gtk
import numpy
import luckylens as ll
import ctypes

xpixels = 512
ypixels = 256

lens = (ll.Lens*3)((0.0, 0.0,  1.),
                   (1.2, 0.0,  2e-2),
                   (1.2, 0.025, 4e-3))
lenses = ll.Lenses(3, lens)
region = ll.Rect(.26, -.05, .46, .05)
count = numpy.zeros((xpixels, ypixels), numpy.int)
magpat = ll.MagPattern(lenses, region, xpixels, ypixels, 0, 0,
                       count.ctypes.data_as(ctypes.POINTER(ctypes.c_int)))

rect = ll.Rect(.9, -.25, 1.4, .25)
ll.rayshoot_rect(magpat, rect, 5000, 5000)
rect = ll.Rect(-1., -.25, -.5, .25)
ll.rayshoot_rect(magpat, rect, 5000, 5000)
buf = numpy.zeros((xpixels, ypixels), numpy.uint8)
ll.image_from_magpat(buf, magpat)

def scale(widget, event):
    global imgscaled
    x, y, width, height = widget.get_allocation()
    m = min(width * ypixels, height * xpixels)
    imgscaled = imgbuf.scale_simple(m//ypixels, m//xpixels, gtk.gdk.INTERP_BILINEAR)
    img.set_from_pixbuf(imgscaled)

w = gtk.Window()
w.connect('destroy', lambda *args: gtk.main_quit())
w.show()

accelgroup = gtk.AccelGroup()
w.add_accel_group(accelgroup)
action = gtk.Action('Quit', None, None, gtk.STOCK_QUIT)
action.connect('activate', lambda *args: gtk.main_quit())
actiongroup = gtk.ActionGroup('SimpleAction')
actiongroup.add_action_with_accel(action, None)
action.set_accel_group(accelgroup)
action.connect_accelerator()

imgmap = gtk.gdk.Pixmap(w.window, xpixels, ypixels)
imgmap.draw_gray_image(w.get_style().fg_gc[gtk.STATE_NORMAL],
                       0, 0, xpixels, ypixels, gtk.gdk.RGB_DITHER_NONE, buf)
imgbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, xpixels, ypixels)
imgbuf.get_from_drawable(imgmap, imgmap.get_colormap(), 0, 0, 0, 0, xpixels, ypixels)
imgscaled = imgbuf.scale_simple(xpixels//2, ypixels//2, gtk.gdk.INTERP_BILINEAR)

img = gtk.Image()
img.set_alignment(0.5, 0.5)
img.set_size_request(50, 50)
img.set_from_pixbuf(imgscaled)
img.show()

w.add(img)

w.connect("configure_event", scale)

gtk.main()

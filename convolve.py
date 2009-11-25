import gobject
import gtk
import gtkimageview
import numpy
import luckylens as ll

class GllConvolve:
    def __init__(self, magpat):
        self.magpat = magpat
        self.running = False
        params = magpat.params[0]
        kernel = numpy.indices((params.ypixels/2, params.xpixels/2))
        kernel = numpy.exp(-sum(kernel*kernel)/8.)
        kernel = numpy.concatenate((kernel, numpy.flipud(kernel)), 0)
        kernel = numpy.concatenate((kernel, numpy.fliplr(kernel)), 1)
        self.kernel = kernel / numpy.sum(kernel)
        self.kernel_fft = numpy.fft.rfft2(self.kernel)
        self.convolved_pattern = None
        self.imageview = gtkimageview.ImageView()
        self.scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        self.scrollwin.show_all()

    def main_widget(self):
        return self.scrollwin

    def start(self):
        self.running = True
        count = self.magpat.get_output("count")
        self.convolved_pattern = numpy.empty_like(count)
        self.convolved_pattern[:] = numpy.fft.irfft2(
            numpy.fft.rfft2(count) * self.kernel_fft)
        buf = numpy.empty(count.shape, numpy.uint8)
        ll.image_from_magpat(buf, self.convolved_pattern)
        self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                                     count.shape[1], count.shape[0])
        self.pixbuf.get_pixels_array()[:] = numpy.dstack([buf]*3)
        gobject.idle_add(self.imageview.set_pixbuf, self.pixbuf)
        self.running = False

    def cancel(self):
        pass

    def get_progress(self):
        if self.running:
            return 0.5
        return 1.0

    def is_running(self):
        return self.running

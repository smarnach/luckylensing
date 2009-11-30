import gobject
import gtk
import gtkimageview
import numpy
import luckylensing as ll

class GllConvolve:
    def __init__(self, magpat):
        self.magpat = magpat
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
        count = self.magpat.get_output("count")
        self.convolved_pattern = numpy.empty_like(count)
        self.convolved_pattern[:] = numpy.fft.irfft2(
            numpy.fft.rfft2(count) * self.kernel_fft)
        buf = numpy.empty(count.shape + (1,), numpy.uint8)
        ll.render_magpattern_greyscale(buf, self.convolved_pattern)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf.repeat(3, axis=2),
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        gobject.idle_add(self.imageview.set_pixbuf, self.pixbuf)

    def cancel(self):
        pass

    def get_progress(self):
        return 0.5

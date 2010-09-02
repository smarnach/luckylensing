import gtkimageview
import gtk
import numpy

class GllImageView(gtkimageview.ImageScrollWin):
    def __init__(self, get_pixbuf):
        self.get_pixbuf = get_pixbuf
        self.imageview = gtkimageview.ImageView()
        self.imageview.set_interpolation(gtk.gdk.INTERP_TILES)
        self.imageview.connect("button-press-event", self.imageview_clicked)
        super(GllImageView, self).__init__(self.imageview)
        self.show_all()
        self.handler = None

    def mark_dirty(self):
        self.imageview.queue_draw()
        if self.handler is None:
            self.handler = self.imageview.connect("expose-event", self.expose)

    def imageview_clicked(self, widget, event, data=None):
        widget.grab_focus()

    def expose(self, *args):
        pixbuf = self.get_pixbuf()
        if isinstance(pixbuf, numpy.ndarray):
            pixbuf = gtk.gdk.pixbuf_new_from_array(
                pixbuf, gtk.gdk.COLORSPACE_RGB, 8)
        self.imageview.set_pixbuf(pixbuf, False)
        self.imageview.disconnect(self.handler)
        self.handler = None

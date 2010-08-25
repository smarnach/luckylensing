import gtkimageview
import gtk
import numpy

class GllImageView(gtkimageview.ImageScrollWin):
    def __init__(self, get_pixbuf, imageview_clicked=None):
        self.get_pixbuf = get_pixbuf
        self.imageview = gtkimageview.ImageView()
        self.imageview.set_interpolation(gtk.gdk.INTERP_TILES)
        if imageview_clicked is not None:
            self.imageview.connect("button-press-event", imageview_clicked)
        else:
            self.imageview.connect("button-press-event", self.imageview_clicked)
        self.imageview.connect("expose-event", self.expose)
        super(GllImageView, self).__init__(self.imageview)
        self.show_all()
        self.dirty = False

    def mark_dirty(self):
        self.dirty = True
        self.imageview.queue_draw()

    def imageview_clicked(self, widget, event, data=None):
        widget.grab_focus()

    def expose(self, *args):
        if self.dirty:
            self.dirty = False
            pixbuf = self.get_pixbuf()
            if isinstance(pixbuf, numpy.ndarray):
                pixbuf = gtk.gdk.pixbuf_new_from_array(
                    pixbuf, gtk.gdk.COLORSPACE_RGB, 8)
            self.imageview.set_pixbuf(pixbuf)
# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import gtkimageview
import gtk

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
        self.imageview.set_pixbuf(self.get_pixbuf(), False)
        self.imageview.disconnect(self.handler)
        self.handler = None

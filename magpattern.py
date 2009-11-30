from math import sqrt, log
from time import clock
import gobject
import gtk
import gtkimageview
import numpy
import luckylensing as ll

class MagPattern(ll.Rayshooter):
    def __init__(self, params):
        super(MagPattern, self).__init__(params, 3)
        self.density = 100
        self.count = None

    def shooting_rectangle(self):
        "Determine sufficiently large shooting rectangle to cover the pattern"
        params = self.params[0]
        lens = [params.lenses.lens[i] for i in range(params.lenses.num_lenses)]
        rect = ll.Rect()
        x0 = min(l.x - sqrt(l.mass) for l in lens)
        d = sum(l.mass/(x0 - l.x) for l in lens)
        rect.x0 = min(x0, params.region.x0 + d)
        x1 = max(l.x + sqrt(l.mass) for l in lens)
        d = sum(l.mass/(x1 - l.x) for l in lens)
        rect.x1 = max(x1, params.region.x1 + d)
        y0 = min(l.y - sqrt(l.mass) for l in lens)
        d = sum(l.mass/(y0 - l.y) for l in lens)
        rect.y0 = min(y0, params.region.y0 + d)
        y1 = max(l.y + sqrt(l.mass) for l in lens)
        d = sum(l.mass/(y1 - l.y) for l in lens)
        rect.y1 = max(y1, params.region.y1 + d)
        return rect

    def start(self):
        params = self.params[0]
        self.count = numpy.zeros((params.ypixels, params.xpixels), numpy.int)
        rect = self.shooting_rectangle()

        # Determine number of rays needed to achieve the ray density
        # specified by self.density (assuming magnification = 1)
        rays = sqrt(self.density) / self.refine_final
        xrays = rays * params.xpixels
        yrays = rays * params.ypixels
        levels = max(0, int(log(min(xrays, yrays))/log(self.refine)))
        xrays /= self.refine**levels
        yrays /= self.refine**levels
        xrays *= (rect.x1 - rect.x0) / (params.region.x1 - params.region.x0)
        yrays *= (rect.y1 - rect.y0) / (params.region.y1 - params.region.y0)
        xrays = int(round(xrays))
        yrays = int(round(yrays))
        self.levels = levels + 2

        print xrays, yrays
        print self.levels

        t = clock()
        super(MagPattern, self).start(self.count, rect, xrays, yrays)
        print clock()-t

    def get_output(self, name):
        if name == "count":
            return self.count
        return None

class GllMagPattern(MagPattern):
    def __init__(self):
        params = ll.MagPatternParams()
        super(GllMagPattern, self).__init__(params)
        self.imageview = gtkimageview.ImageView()
        self.scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        self.scrollwin.show_all()
        self.dragger = self.imageview.get_tool()
        self.selector = gtkimageview.ImageToolSelector(self.imageview)
        self.selector.connect("selection-changed", self.update_selection)
        self.imageview.connect("button-press-event", self.imageview_clicked)
        self.imageview.connect("key-press-event", self.imageview_key_pressed)
        self.builder = gtk.Builder()
        self.builder.add_from_file("magpattern.glade")
        self.builder.connect_signals(self)
        self.lens_list = self.builder.get_object("lens_list")
        self.fix_adjustments()
        self.set_params_from_ui()

    def imageview_clicked(self, widget, event, data=None):
        widget.grab_focus()
        if event.button == 2:
            # widget.set_tool(self.dragger)
            draw_rect = self.imageview.get_draw_rect()
            zoom = self.imageview.get_zoom()
            viewport = self.imageview.get_viewport()
            source_x = (event.x - draw_rect.x) / zoom + viewport.x
            source_y = (event.y - draw_rect.y) / zoom + viewport.y
            params = self.params[0]
            source_r = .005 * params.xpixels / (params.region.x1 - params.region.x0)
            self.show_source_images(source_x, source_y, source_r);
        if event.button == 3:
            widget.set_tool(self.selector)

    def imageview_key_pressed(self, widget, event, data=None):
        if event.string == "h":
            self.show_hit_pattern()
            return True

    def update_selection(self, selector):
        rect = selector.get_selection()
        params = self.params[0]
        region = params.region
        width = max(rect.width, rect.height*params.xpixels/params.ypixels)
        x = rect.x + (rect.width - width)/2
        xfactor = (region.x1-region.x0)/params.xpixels
        x0 = region.x0 + x * xfactor
        x1 = x0 + width * xfactor
        height = max(rect.height, rect.width*params.ypixels/params.xpixels)
        y = rect.y + (rect.height - height)/2
        yfactor = (region.y1-region.y0)/params.ypixels
        y0 = region.y0 + y * yfactor
        y1 = y0 + width * yfactor
        self.builder.get_object("region_x0").set_value(x0)
        self.builder.get_object("region_y0").set_value(y0)
        self.builder.get_object("region_x1").set_value(x1)
        self.builder.get_object("region_y1").set_value(y1)

    def fix_adjustments(self):
        self.builder.get_object("xpixels").set_value(1024)
        self.builder.get_object("ypixels").set_value(1024)
        self.builder.get_object("region_x0").set_value(-.1)
        self.builder.get_object("region_y0").set_value(-.3)
        self.builder.get_object("region_x1").set_value( .5)
        self.builder.get_object("region_y1").set_value( .3)
        self.builder.get_object("density").set_value(100)

    def set_params_from_ui(self):
        params = self.params[0]
        params.lenses = ll.Lenses(self.lens_list)
        params.xpixels = int(self.builder.get_object("xpixels").get_value())
        params.ypixels = int(self.builder.get_object("ypixels").get_value())
        params.region.x0 = self.builder.get_object("region_x0").get_value()
        params.region.y0 = self.builder.get_object("region_y0").get_value()
        params.region.x1 = self.builder.get_object("region_x1").get_value()
        params.region.y1 = self.builder.get_object("region_y1").get_value()
        self.density = self.builder.get_object("density").get_value()

    def main_widget(self):
        return self.scrollwin

    def config_widget(self):
        return self.builder.get_object("config")

    def edit_lens_cell0(self, cell, path, new_text):
        self.lens_list[path][0] = float(new_text)
        return
    def edit_lens_cell1(self, cell, path, new_text):
        self.lens_list[path][1] = float(new_text)
        return
    def edit_lens_cell2(self, cell, path, new_text):
        self.lens_list[path][2] = float(new_text)
        return

    def start(self):
        self.set_params_from_ui()
        super(GllMagPattern, self).start()
        if self.cancel_flag:
            return
        buf = numpy.empty(self.count.shape + (1,), numpy.uint8)
        ll.image_from_magpat(buf, self.count)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf.repeat(3, axis=2),
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        gobject.idle_add(self.imageview.set_tool, self.dragger)
        gobject.idle_add(self.imageview.set_pixbuf, self.pixbuf)

    def show_hit_pattern(self):
        params = self.params[0]
        buf = numpy.empty((params.xpixels, params.ypixels, 1), numpy.uint8)
        rect = self.shooting_rectangle()
        params.ray_hit_pattern(buf, rect)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf.repeat(3, axis=2),
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        self.imageview.set_tool(self.dragger)
        self.imageview.set_pixbuf(self.pixbuf)

    def show_source_images(self, source_x, source_y, source_r):
        params = self.params[0]
        buf = numpy.zeros((params.xpixels, params.ypixels, 1), numpy.uint8)
        rect = self.shooting_rectangle()
        params.source_images(buf, rect, params.xpixels, params.ypixels, 2,
                             source_x, source_y, source_r)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf.repeat(3, axis=2),
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        self.imageview.set_tool(self.dragger)
        self.imageview.set_pixbuf(self.pixbuf)

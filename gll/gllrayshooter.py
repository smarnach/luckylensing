import sys
sys.path.append("../libll")

import gobject
import gtk
import gtkimageview
import numpy
import luckylensing as ll
import rayshooter

class GllRayshooter(gobject.GObject):
    __gsignals__ = {
        "run-pipeline": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        super(GllRayshooter, self).__init__()
        self.rayshooter = rayshooter.Rayshooter()
        self.imageview = gtkimageview.ImageView()
        self.imageview.set_interpolation(gtk.gdk.INTERP_TILES)
        self.scrollwin = gtkimageview.ImageScrollWin(self.imageview)
        self.scrollwin.show_all()
        self.dragger = self.imageview.get_tool()
        self.selector = gtkimageview.ImageToolSelector(self.imageview)
        self.selector.connect("selection-changed", self.update_selection)
        self.imageview.connect("button-press-event", self.imageview_clicked)
        self.imageview.connect("key-press-event", self.imageview_key_pressed)
        self.builder = gtk.Builder()
        self.builder.add_from_file("gllrayshooter.glade")
        self.builder.connect_signals(self)
        self.lens_list = self.builder.get_object("lens_list")
        self.lens_selection = self.builder.get_object("treeview").get_selection()
        self.lens_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.fix_adjustments()
        self.set_params_from_ui()
        self.history = []
        self.history_pos = -1

    def imageview_clicked(self, widget, event, data=None):
        widget.grab_focus()
        if event.button == 1:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self.emit("run-pipeline")
        elif event.button == 2:
            draw_rect = self.imageview.get_draw_rect()
            zoom = self.imageview.get_zoom()
            viewport = self.imageview.get_viewport()
            source_x = (event.x - draw_rect.x) / zoom + viewport.x
            source_y = (event.y - draw_rect.y) / zoom + viewport.y
            params = self.rayshooter.params[0]
            source_r = .005 * params.xpixels / params.region.width
            self.show_source_images(source_x, source_y, source_r);
        if event.button == 3:
            if widget.get_tool() is self.dragger:
                widget.set_tool(self.selector)
            else:
                widget.set_tool(self.dragger)

    def imageview_key_pressed(self, widget, event, data=None):
        if event.string == "h":
            self.show_hit_pattern()
            return True

    def update_selection(self, selector):
        rect = selector.get_selection()
        params = self.rayshooter.params[0]
        region = params.region
        width = max(rect.width, rect.height*params.xpixels/params.ypixels)
        x = rect.x + (rect.width - width)/2
        xfactor = region.width/params.xpixels
        x0 = region.x + x * xfactor
        x1 = x0 + width * xfactor
        height = max(rect.height, rect.width*params.ypixels/params.xpixels)
        y = rect.y + (rect.height - height)/2
        yfactor = region.height/params.ypixels
        y0 = region.y + y * yfactor
        y1 = y0 + height * yfactor
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
        self.builder.get_object("kernel_triangulated").set_active(True)

    def set_params_from_ui(self):
        self.imageview.grab_focus()
        params = self.rayshooter.params[0]
        lenses = []
        for l in self.lens_list:
            if l[0]:
                lenses.append(tuple(l)[1:])
        params.lenses = ll.Lenses(lenses)
        params.xpixels = int(self.builder.get_object("xpixels").get_value())
        params.ypixels = int(self.builder.get_object("ypixels").get_value())
        params.region.x = self.builder.get_object("region_x0").get_value()
        params.region.y = self.builder.get_object("region_y0").get_value()
        x1 = self.builder.get_object("region_x1").get_value()
        params.region.width = x1 - params.region.x
        y1 = self.builder.get_object("region_y1").get_value()
        params.region.height = y1 - params.region.y
        self.rayshooter.density = self.builder.get_object("density").get_value()
        if self.builder.get_object("kernel_simple").get_active():
            self.rayshooter.kernel = ll.KERNEL_SIMPLE
        elif self.builder.get_object("kernel_bilinear").get_active():
            self.rayshooter.kernel = ll.KERNEL_BILINEAR
        elif self.builder.get_object("kernel_triangulated").get_active():
            self.rayshooter.kernel = ll.KERNEL_TRIANGULATED
        self.history_params = (map(tuple, self.lens_list),
                               params.xpixels, params.ypixels,
                               (params.region.x, params.region.y,
                                params.region.width, params.region.height),
                               self.rayshooter.density, self.rayshooter.kernel)

    def main_widget(self):
        return self.scrollwin

    def config_widget(self):
        return self.builder.get_object("config")

    def toggle_lens(self, cell, path):
        self.lens_list[path][0] ^= True
    def edit_lens_cell1(self, cell, path, new_text):
        self.lens_list[path][1] = float(new_text)
    def edit_lens_cell2(self, cell, path, new_text):
        self.lens_list[path][2] = float(new_text)
    def edit_lens_cell3(self, cell, path, new_text):
        self.lens_list[path][3] = float(new_text)

    def add_lens(self, button):
        self.lens_list.append((True, 0.0, 0.0, 0.0))

    def delete_lens(self, button):
        lens_list, selected = self.lens_selection.get_selected_rows()
        for row_path in reversed(selected):
            lens_list.remove(lens_list.get_iter(row_path))

    def _update_pixbuf(self):
        colors = [(0, 0, 0), (0, 0, 255), (32, 0, 255),
                  (255, 0, 0), (255, 255, 0), (255, 255, 255)]
        steps = [255, 32, 255, 255, 255]
        buf = ll.render_magpattern_gradient(self.rayshooter.count, colors, steps)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf,
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        gobject.idle_add(self.imageview.set_tool, self.dragger)
        gobject.idle_add(self.imageview.set_pixbuf, self.pixbuf)

    def run(self, num_threads=2):
        self.set_params_from_ui()
        self.rayshooter.run(num_threads)
        if self.rayshooter.cancel_flag:
            return
        self.history_pos += 1
        del self.history[self.history_pos:]
        self.history.append((self.history_params, numpy.array(self.rayshooter.count)))
        self._update_pixbuf()

    def cancel(self):
        self.rayshooter.cancel()

    def get_progress(self):
        return self.rayshooter.get_progress()

    def _restore_from_history(self):
        history_params = self.history[self.history_pos][0]
        self.rayshooter.count = self.history[self.history_pos][1]
        params = self.rayshooter.params[0]
        lenses = []
        self.lens_list.clear()
        for l in history_params[0]:
            self.lens_list.append(l)
            if l[0]:
                lenses.append(l[1:])
        params.lenses = ll.Lenses(lenses)
        params.xpixels = history_params[1]
        params.ypixels = history_params[2]
        params.region = ll.Rect(*history_params[3])
        self.rayshooter.density = history_params[4]
        self.rayshooter.kernel = history_params[5]

        self.builder.get_object("xpixels").set_value(params.xpixels)
        self.builder.get_object("ypixels").set_value(params.ypixels)
        self.builder.get_object("region_x0").set_value(params.region.x)
        self.builder.get_object("region_y0").set_value(params.region.y)
        x1 = params.region.x + params.region.width
        self.builder.get_object("region_x1").set_value(x1)
        y1 = params.region.y + params.region.height
        self.builder.get_object("region_y1").set_value(y1)
        self.builder.get_object("density").set_value(self.rayshooter.density)
        if self.rayshooter.kernel == ll.KERNEL_SIMPLE:
            self.builder.get_object("kernel_simple").set_active(True)
        elif self.rayshooter.kernel == ll.KERNEL_BILINEAR:
            self.builder.get_object("kernel_bilinear").set_active(True)
        elif self.rayshooter.kernel == ll.KERNEL_TRIANGULATED:
            self.builder.get_object("kernel_triangulated").set_active(True)
        self._update_pixbuf()

    def back(self):
        if self.history_pos > 0:
            self.history_pos -= 1
            self._restore_from_history()

    def forward(self):
        if self.history_pos < len(self.history) - 1:
            self.history_pos += 1
            self._restore_from_history()

    def show_hit_pattern(self):
        params = self.rayshooter.params[0]
        buf = numpy.empty((params.xpixels, params.ypixels, 1), numpy.uint8)
        rect = self.rayshooter.get_shooting_params()[0]
        params.ray_hit_pattern(buf, rect)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf.repeat(3, axis=2),
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        self.imageview.set_tool(self.dragger)
        self.imageview.set_pixbuf(self.pixbuf)

    def show_source_images(self, source_x, source_y, source_r):
        params = self.rayshooter.params[0]
        buf = numpy.zeros((params.xpixels, params.ypixels, 1), numpy.uint8)
        rect = self.rayshooter.get_shooting_params()[0]
        params.source_images(buf, rect, params.xpixels, params.ypixels, 2,
                             source_x, source_y, source_r)
        self.pixbuf = gtk.gdk.pixbuf_new_from_array(buf.repeat(3, axis=2),
                                                    gtk.gdk.COLORSPACE_RGB, 8)
        self.imageview.set_tool(self.dragger)
        self.imageview.set_pixbuf(self.pixbuf)

gobject.type_register(GllRayshooter)

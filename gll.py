#!/usr/bin/env python
import gobject
import threading
import gtk
import pyconsole
import numpy
import luckylens as ll
from magpattern import GllMagPattern
from convolve import GllConvolve

xpixels = 1024
ypixels = 1024

class GllApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("gll.glade")
        self.builder.connect_signals(self)

        self.lens_list = self.builder.get_object("lens_list")
        self.vbox = self.builder.get_object("vbox")
        self.statusbar = self.builder.get_object("statusbar")
        self.progressbar = self.builder.get_object("progressbar")

        self.mode = 0

    def generate_pattern(self, *args):
        params = ll.MagPatternParams(self.lens_list, (-.005, -.01, .015, .01),
                                     xpixels, ypixels)
#        params = ll.MagPatternParams(self.lens_list, (.26, -.1, .46, .1),
#                                     xpixels, ypixels)
        if self.mode == 1:
            self.vbox.remove(self.magpattern.main_widget())
        elif self.mode == 2:
            self.vbox.remove(self.convolve.main_widget())
        self.magpattern = GllMagPattern(params)
        self.magpattern.density = 5
        self.vbox.pack_start(self.magpattern.main_widget())
        self.mode = 1
        self.init_progressbar(self.magpattern)
        threading.Thread(target=self.magpattern.start).start()

    def convolve_pattern(self, *args):
        self.convolve = GllConvolve(self.magpattern)
        if self.mode != 2:
            self.vbox.remove(self.magpattern.main_widget())
            self.vbox.pack_start(self.convolve.main_widget())
            self.mode = 2
        self.init_progressbar(self.convolve)
        threading.Thread(target=self.convolve.start).start()

    def extract_light_curve(self, *args):
        pass

    def init_progressbar(self, comp):
        self.progressbar.set_property("show-text", True)
        gobject.timeout_add(100, self.update_progressbar, comp)

    def update_progressbar(self, comp):
        if comp.is_running():
            self.progressbar.set_fraction(min(comp.get_progress(), 1.0))
        else:
            self.progressbar.set_property("show-text", False)
            self.progressbar.set_fraction(0.0)
            return False
        return True

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
        self.magpattern.cancel()
        gtk.main_quit()

gobject.threads_init()
app = GllApp()
gtk.main()

#!/usr/bin/env python
import gobject
import threading
import gtk
import pyconsole
from magpattern import GllMagPattern
from convolve import GllConvolve

class GllApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("gll.glade")
        self.builder.connect_signals(self)

        self.hpaned = self.builder.get_object("hpaned")
        self.statusbar = self.builder.get_object("statusbar")
        self.progressbar = self.builder.get_object("progressbar")

        self.magpattern = GllMagPattern()
        self.hpaned.pack1(self.magpattern.main_widget(), resize=True)
        self.hpaned.pack2(self.magpattern.config_widget(), resize=False)

    def generate_pattern(self, *args):
        thread = threading.Thread(target=self.magpattern.start)
        self.init_progressbar(self.magpattern, thread)
        thread.start()

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

    def init_progressbar(self, comp, thread):
        self.progressbar.set_property("show-text", True)
        gobject.timeout_add(100, self.update_progressbar, comp, thread)

    def update_progressbar(self, comp, thread):
        if thread.isAlive():
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

    def quit_app(self, *args):
        self.magpattern.cancel()
        gtk.main_quit()

gobject.threads_init()
app = GllApp()
gtk.main()

#!/usr/bin/env python
import threading
from time import sleep
import gobject
import gtk
from gllrayshooter import GllRayshooter
try:
    import pyconsole
except:
    pyconsole = None

class GllApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("gll.glade")
        self.builder.connect_signals(self)

        self.hpaned = self.builder.get_object("hpaned")
        self.statusbar = self.builder.get_object("statusbar")
        self.progressbar = self.builder.get_object("progressbar")
        if not pyconsole:
            self.builder.get_object("toolbutton_console").hide()

        self.plugin = GllRayshooter()
        self.plugin.connect("run-pipeline", self.run_pipeline)
        self.plugin.connect("cancel-pipeline", self.cancel_pipeline)
        self.plugin.connect("history-back", self.history_back)
        self.plugin.connect("history-forward", self.history_forward)
        self.hpaned.pack1(self.plugin.main_widget, resize=True)
        self.hpaned.pack2(self.plugin.config_widget, resize=False)

        self.running = threading.Lock()

    def run_pipeline(self, *args):
        if not self.running.acquire(False):
            return
        self.cancel_flag = False
        data = {}
        for plugin in [self.plugin]:
            self.current_processor = plugin.processor
            data.update(plugin.get_config())
            thread = threading.Thread(target=plugin.processor.update,
                                      args=(data,))
            self.init_progressbar()
            thread.start()
            while thread.isAlive():
                gobject.main_context_default().iteration(False)
                sleep(0.02)
            if self.cancel_flag:
                break
            plugin.update(data)
        del self.current_processor
        self.running.release()

    def history_back(self, *args):
        pass

    def history_forward(self, *args):
        pass

    def cancel_pipeline(self, *args):
        proc = self.__dict__.get("current_processor")
        if proc:
            self.current_processor.cancel()
        self.cancel_flag = True

    def init_progressbar(self):
        self.progressbar.set_property("show-text", True)
        gobject.timeout_add(100, self.update_progressbar)

    def update_progressbar(self):
        proc = self.__dict__.get("current_processor")
        if proc:
            self.progressbar.set_fraction(min(proc.get_progress(), 1.0))
            return True
        else:
            self.progressbar.set_property("show-text", False)
            self.progressbar.set_fraction(0.0)
            return False

    def show_console(self, *args):
        if not pyconsole:
            return
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
        self.cancel_pipeline()
        gtk.main_quit()

gobject.threads_init()
app = GllApp()
gtk.main()

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

        self.running = threading.Lock()
        self.history = []
        self.history_pos = -1
        self.serial = 0
        self.active_plugin = None
        self.plugins = []
        self.add_plugin(GllRayshooter())

    def add_plugin(self, plugin):
        self.plugins.append(plugin)
        plugin.connect("run-pipeline", self.run_pipeline)
        plugin.connect("cancel-pipeline", self.cancel_pipeline)
        plugin.connect("history-back", self.history_back)
        plugin.connect("history-forward", self.history_forward)
        self.activate_plugin(plugin)

    def activate_plugin(self, plugin):
        if self.active_plugin:
            self.hpaned.remove(self.active_plugin.main_widget)
            self.hpaned.remove(self.active_plugin.config_widget)
        self.hpaned.pack1(plugin.main_widget, resize=True)
        self.hpaned.pack2(plugin.config_widget, resize=False)
        self.active_plugin = plugin

    def pipeline_thread(self):
        data = {}
        data_serials = {}
        self.serial += 1
        history_entry = []
        for plugin in self.plugins:
            self.active_processor = plugin.processor
            config = plugin.get_config()
            history_entry.append((plugin, config))
            data.update(config)
            data_serials.update(dict.fromkeys(config, self.serial))
            plugin.processor.update(data, data_serials, self.serial)
            if self.cancel_flag:
                break
            gobject.idle_add(plugin.update, data)
            while gobject.main_context_default().iteration(False):
                pass
        del self.active_processor
        if not self.cancel_flag:
            if self.history_pos < len(self.history) - 1:
                del self.history[self.history_pos+1:]
                serials = [s for s, entry in self.history] + [self.serial]
                for plugin, config in self.history[self.history_pos][1]:
                    plugin.processor.restrict_history(serials)
            self.history.append((self.serial, history_entry))
            self.history_pos += 1
        self.running.release()

    def run_pipeline(self, *args):
        if not self.running.acquire(False):
            return
        self.cancel_flag = False
        self.progressbar.set_property("show-text", True)
        gobject.timeout_add(100, self.update_progressbar)
        threading.Thread(target=self.pipeline_thread).start()

    def restore(self):
        data = {}
        serial, history_entry = self.history[self.history_pos]
        self.plugins = []
        active_plugin_found = False
        for plugin, config in history_entry:
            self.plugins.append(plugin)
            if plugin is self.active_plugin:
                active_plugin_found = True
            plugin.set_config(config)
            data.update(config)
            plugin.processor.restore(data, serial)
            plugin.update(data)
        if not active_plugin_found:
            self.activate_plugin(self.plugins[0])

    def history_back(self, *args):
        if self.history_pos <= 0:
            return
        self.history_pos -= 1
        self.restore()

    def history_forward(self, *args):
        if self.history_pos >= len(self.history) - 1:
            return
        self.history_pos += 1
        self.restore()

    def cancel_pipeline(self, *args):
        proc = self.__dict__.get("active_processor")
        if proc:
            self.active_processor.cancel()
        self.cancel_flag = True

    def update_progressbar(self):
        proc = self.__dict__.get("active_processor")
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

#!/usr/bin/env python
import threading
import gobject
import gtk
from gllplugin import GllPlugin
from gllrayshooter import GllRayshooter
from globularcluster import GlobularCluster
from glllenses import GllLenses
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
        self.vpaned = self.builder.get_object("vpaned")
        self.statusbar = self.builder.get_object("statusbar")
        self.progressbar = self.builder.get_object("progressbar")
        if not pyconsole:
            self.builder.get_object("toolbutton_console").hide()
        self.init_plugins()

        self.running = threading.Lock()
        self.active_processor = None
        self.history = []
        self.history_pos = -1
        self.serial = 0
        self.add_plugin(GllPlugin(GlobularCluster()))
        self.add_plugin(GllLenses())
        self.add_plugin(GllRayshooter())

    def init_plugins(self):
        self.plugins = gtk.ListStore(bool, str, GllPlugin)
        treeview = gtk.TreeView(self.plugins)
        column = gtk.TreeViewColumn("Enabled")
        renderer = gtk.CellRendererToggle()
        renderer.connect("toggled", self.toggle_plugin)
        column.pack_start(renderer)
        column.add_attribute(renderer, 'active', 0)
        treeview.append_column(column)
        column = gtk.TreeViewColumn("Name")
        renderer = gtk.CellRendererText()
        renderer.connect("edited", self.edit_plugin_name)
        column.pack_start(renderer, True)
        column.add_attribute(renderer, 'text', 1)
        treeview.append_column(column)
        treeview.set_headers_visible(False)
        treeview.get_selection().connect("changed",
                                         self.selected_plugin_changed)
        treeview.show_all()
        self.builder.get_object("pipeline_frame").add(treeview)
        self.selected_plugin = None

    def add_plugin(self, plugin):
        if hasattr(plugin, "name"):
            name = plugin.name
        else:
            name = plugin.processor.__class__.__name__
        self.plugins.append((True, name, plugin))
        plugin.connect("run-pipeline", self.run_pipeline)
        plugin.connect("cancel-pipeline", self.cancel_pipeline)
        plugin.connect("history-back", self.history_back)
        plugin.connect("history-forward", self.history_forward)
        self.select_plugin(plugin)

    def select_plugin(self, plugin):
        if plugin.main_widget:
            child = self.hpaned.get_child1()
            if child:
                self.hpaned.remove(child)
            self.hpaned.pack1(plugin.main_widget, resize=True)
        if plugin.config_widget:
            child = self.vpaned.get_child2()
            if child:
                self.vpaned.remove(child)
            self.vpaned.pack2(plugin.config_widget, resize=True)
        self.selected_plugin = plugin

    def selected_plugin_changed(self, selection):
        list, it = selection.get_selected()
        if it is not None:
            self.select_plugin(list[it][2])

    def pipeline_thread(self):
        data = {}
        data_serials = {}
        self.serial += 1
        for active, name, plugin in self.plugins:
            if not active:
                continue
            self.active_processor = plugin.processor
            plugin.update_config(data, data_serials, self.serial)
            if plugin.processor:
                plugin.processor.update(data, data_serials, self.serial)
            if self.cancel_flag:
                break
            gobject.idle_add(plugin.update, data)
            while gobject.main_context_default().iteration(False):
                pass
        self.active_processor = None
        self.progressbar_active = False
        if not self.cancel_flag:
            if self.history_pos < len(self.history) - 1:
                del self.history[self.history_pos+1:]
                serials = [s for s, plugin in self.history] + [self.serial]
                for plugin in self.history[self.history_pos][1]:
                    if plugin.processor:
                        plugin.processor.restrict_history(serials)
                    plugin.restrict_history(serials)
            self.history.append((self.serial, map(tuple, self.plugins)))
            self.history_pos += 1
        self.running.release()

    def run_pipeline(self, *args):
        if not self.running.acquire(False):
            return
        self.cancel_flag = False
        self.progressbar.set_property("show-text", True)
        self.progressbar_active = True
        gobject.timeout_add(100, self.update_progressbar)
        threading.Thread(target=self.pipeline_thread).start()

    def restore(self):
        data = {}
        serial, plugins = self.history[self.history_pos]
        selected_plugin_found = False
        self.plugins.clear()
        for active, name, plugin in plugins:
            self.plugins.append((active, name, plugin))
            if plugin is self.selected_plugin:
                selected_plugin_found = True
            if active:
                plugin.restore_config(data, serial)
                if plugin.processor:
                    plugin.processor.restore(data, serial)
                plugin.update(data)
        if not selected_plugin_found:
            self.select_plugin(plugin=self.plugins[0][2])

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
        proc = self.active_processor
        if proc:
            proc.cancel()
        self.cancel_flag = True

    def update_progressbar(self):
        proc = self.active_processor
        if proc:
            self.progressbar.set_fraction(min(proc.get_progress(), 1.0))
        if self.progressbar_active:
            return True
        self.progressbar.set_property("show-text", False)
        self.progressbar.set_fraction(0.0)
        return False

    def toggle_plugin(self, cell, path):
        self.plugins[path][0] ^= True

    def edit_plugin_name(self, cell, path, new_text):
        self.plugins[path][1] = new_text

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

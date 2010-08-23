#!/usr/bin/env python

import sys
sys.path.append("../libll")

import threading
import gobject
import gtk
from gllplugin import GllPlugin
from gllglobularcluster import GllGlobularCluster
from glllenses import GllLenses
from gllrayshooter import GllRayshooter
from gllsourcestar import GllGaussianSource, GllFlatSource
from gllsourcepath import GllSourcePath
from gllconvolution import GllConvolution
from glllightcurve import GllLightCurve
try:
    import pyconsole
except:
    pyconsole = None

class GllApp(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("gll.glade")
        self.builder.connect_signals(self)

        self.main_box = self.builder.get_object("main_box")
        self.config_box = self.builder.get_object("config_box")
        self.config_label = self.builder.get_object("config_label")
        self.progressbar = self.builder.get_object("progressbar")
        if not pyconsole:
            self.builder.get_object("toolbutton_console").hide()
        self.init_plugins()

        self.running = threading.Lock()
        self.active_processor = None
        self.history = []
        self.history_pos = -1
        self.serial = 0
        self.add_plugin(GllGlobularCluster())
        self.add_plugin(GllLenses())
        it = self.add_plugin(GllRayshooter())
        self.add_plugin(GllSourcePath())
        self.add_plugin(GllGaussianSource())
        self.add_plugin(GllFlatSource())
        self.add_plugin(GllConvolution())
        self.add_plugin(GllLightCurve())
        self.selection.select_iter(it)

    def init_plugins(self):
        self.plugins = gtk.ListStore(bool, str, GllPlugin, int)
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
        self.selection = treeview.get_selection()
        self.selection.connect("changed", self.selected_plugin_changed)
        treeview.show_all()
        self.builder.get_object("pipeline_window").add(treeview)
        self.treeview = treeview

    def add_plugin(self, plugin):
        if hasattr(plugin, "name"):
            name = plugin.name
        else:
            name = plugin.processor.__class__.__name__
        it = self.plugins.append((True, name, plugin, -1))
        self.selection.select_iter(it)
        plugin.connect("run-pipeline", self.run_pipeline)
        plugin.connect("cancel-pipeline", self.cancel_pipeline)
        plugin.connect("history-back", self.history_back)
        plugin.connect("history-forward", self.history_forward)
        return it

    def selected_plugin_changed(self, selection):
        plugins, it = selection.get_selected()
        child = self.config_box.get_child()
        if child:
            self.config_box.remove(child)
        if it is not None:
            plugin = plugins[it][2]
            name = plugins[it][1]
            if plugin.main_widget:
                child = self.main_box.get_child()
                if child:
                    self.main_box.remove(child)
                self.main_box.add(plugin.main_widget)
            self.config_label.set_text(name)
            if plugin.config_widget:
                self.config_box.add(plugin.config_widget)
        else:
            self.config_label.set_text("")

    def pipeline_thread(self):
        data = {}
        data_serials = {}
        for i, (active, name, plugin, last_serial) in enumerate(self.plugins):
            if not active:
                continue
            self.serial += 1
            self.active_processor = plugin.processor
            plugin.update_config(data, data_serials, self.serial, last_serial)
            if plugin.processor:
                plugin.processor.update(data, data_serials, self.serial)
            if self.cancel_flag:
                break
            self.plugins[i][3] = self.serial
            gobject.idle_add(plugin.update, data)
            while gobject.main_context_default().iteration(False):
                pass
        self.active_processor = None
        self.progressbar_active = False
        if not self.cancel_flag:
            self.save_to_history()
        self.running.release()

    def run_pipeline(self, *args):
        if not self.running.acquire(False):
            return
        self.cancel_flag = False
        self.treeview.grab_focus()
        self.progressbar.set_property("show-text", True)
        self.progressbar_active = True
        self.progressbar.set_fraction(0.0)
        gobject.timeout_add(100, self.update_progressbar)
        threading.Thread(target=self.pipeline_thread).start()

    def save_to_history(self):
        truncate = self.history_pos < len(self.history) - 1
        if truncate:
            del self.history[self.history_pos+1:]
        self.history.append(map(tuple, self.plugins))
        if truncate:
            for active, name, plugin, serial in self.history[self.history_pos]:
                serials = []
                for plugins in self.history:
                    for entry in plugins:
                        if entry[2] is plugin:
                            serials.append(entry[3])
                if plugin.processor:
                    plugin.processor.restrict_history(serials)
                plugin.restrict_history(serials)
        self.history_pos += 1

    def restore_from_history(self):
        data = {}
        plugins, it = self.selection.get_selected()
        if it:
            selected_plugin = plugins[it][2]
        else:
            selected_plugin = None
        plugins.clear()
        for active, name, plugin, serial in self.history[self.history_pos]:
            it = plugins.append((active, name, plugin, serial))
            if plugin is selected_plugin:
                self.selection.select_iter(it)
            if active:
                plugin.restore_config(data, serial)
                if plugin.processor:
                    plugin.processor.restore(data, serial)
                plugin.update(data)

    def history_back(self, *args):
        if self.history_pos <= 0:
            return
        self.history_pos -= 1
        self.restore_from_history()

    def history_forward(self, *args):
        if self.history_pos >= len(self.history) - 1:
            return
        self.history_pos += 1
        self.restore_from_history()

    def cancel_pipeline(self, *args):
        proc = self.active_processor
        if proc:
            proc.cancel()
        self.cancel_flag = True

    def update_progressbar(self):
        proc = self.active_processor
        if proc:
            fraction = min(max(proc.get_progress(), 0.0), 1.0)
            self.progressbar.set_fraction(fraction)
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

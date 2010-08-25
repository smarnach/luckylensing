#!/usr/bin/env python
# -*- coding: latin-1 -*-

import sys
sys.path.append("../libll")

import threading
import cPickle as pickle
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

all_plugins = {"Globular cluster": GllGlobularCluster,
               "Lens list": GllLenses,
               "Magnification pattern": GllRayshooter,
               "Gaussian source profile": GllGaussianSource,
               "Flat source profile": GllFlatSource,
               "Source path": GllSourcePath,
               "Convolution": GllConvolution,
               "Light curve": GllLightCurve}

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
        self.filename = None
        if len(sys.argv) > 1:
            self.filename = sys.argv[1]
            self.read_pipeline(self.filename)

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
        treeview.set_reorderable(True)
        self.selection = treeview.get_selection()
        self.selection.connect("changed", self.selected_plugin_changed)
        treeview.show_all()
        self.builder.get_object("pipeline_window").add(treeview)
        self.treeview = treeview
        addmenu = gtk.Menu()
        for name in sorted(all_plugins.keys()):
            item = gtk.MenuItem(name)
            item.connect("activate", self.add_plugin_activated, name)
            addmenu.append(item)
        addmenu.show_all()
        addbutton = self.builder.get_object("addbutton")
        addbutton.set_menu(addmenu)
        self.arrowbutton = addbutton.get_child().get_children()[1]
        addbutton.connect("clicked", self.popup_addmenu, True)

    def popup_addmenu(self, *args):
        self.arrowbutton.set_active(True)

    def add_plugin_activated(self, menuitem, name):
        self.add_plugin(name)

    def add_plugin(self, name, active=True):
        plugin = all_plugins[name]()
        it = self.plugins.append((active, name, plugin, -1))
        self.selection.select_iter(it)
        plugin.connect("run-pipeline", self.run_pipeline)
        plugin.connect("cancel-pipeline", self.cancel_pipeline)
        plugin.connect("history-back", self.history_back)
        plugin.connect("history-forward", self.history_forward)
        return plugin

    def remove_plugin_widgets(self):
        child = self.config_box.get_child()
        if child:
            self.config_box.remove(child)
        child = self.main_box.get_child()
        if child:
            self.main_box.remove(child)

    def remove_plugin(self, *args):
        plugins, it = self.selection.get_selected()
        if it is not None:
            self.remove_plugin_widgets()
            if plugins.remove(it):
                self.selection.select_iter(it)
            elif len(plugins):
                self.selection.select_path(len(plugins)-1)

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

    def new_pipeline(self, *args):
        if len(self.plugins):
            message = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION,
                                        buttons=gtk.BUTTONS_YES_NO)
            message.set_markup("Clear the current pipeline?")
            response = message.run()
            message.destroy()
            if response == gtk.RESPONSE_NO:
                return
        self.remove_plugin_widgets()
        self.plugins.clear()
        self.filename = None

    def write_pipeline(self, filename):
        plugins = []
        for active, name, plugin, last_serial in self.plugins:
            plugins.append((active, name, plugin.get_config()))
        it = self.selection.get_selected()[1]
        if it is None:
            selected = 0
        else:
            selected = self.plugins.get_path(it)[0]
        f = open(filename, "w")
        pickle.dump(plugins, f)
        pickle.dump(selected, f)
        f.close()
        self.filename = filename

    def read_pipeline(self, filename):
        f = open(filename)
        plugins = pickle.load(f)
        selected = pickle.load(f)
        f.close()
        for active, name, config in plugins:
            plugin = self.add_plugin(name, active)
            plugin.set_config(config)
        self.selection.select_path(selected)

    def save_pipeline_as(self, *args):
        dialog = gtk.FileChooserDialog(
            "Save Pipeline", action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        dialog.set_do_overwrite_confirmation(True)
        filt = gtk.FileFilter()
        filt.set_name("GLL Pipeline Files")
        filt.add_pattern("*.gll")
        dialog.set_filter(filt)
        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()
        if response != gtk.RESPONSE_ACCEPT:
            return
        self.write_pipeline(filename)

    def save_pipeline(self, *args):
        if not len(self.plugins):
            return
        if not self.filename:
            self.save_pipeline_as()
        else:
            self.write_pipeline(self.filename)

    def open_pipeline(self, arg=None, append=False):
        dialog = gtk.FileChooserDialog(
            "Open Pipeline", action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
        filt = gtk.FileFilter()
        filt.set_name("GLL Pipeline Files")
        filt.add_pattern("*.gll")
        dialog.set_filter(filt)
        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()
        if response != gtk.RESPONSE_ACCEPT:
            return
        if not append:
            self.remove_plugin_widgets()
            self.plugins.clear()
            self.filename = filename
        self.read_pipeline(filename)

    def append_to_pipeline(self, *args):
        self.open_pipeline(append=True)

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
        main_widget = self.main_box.get_child()
        main_widget_found = False
        plugins.clear()
        for active, name, plugin, serial in self.history[self.history_pos]:
            it = plugins.append((active, name, plugin, serial))
            if plugin is selected_plugin:
                self.selection.select_iter(it)
            if plugin.main_widget is main_widget:
                main_widget_found = True
            if active:
                plugin.restore_config(data, serial)
                if plugin.processor:
                    plugin.processor.restore(data, serial)
                plugin.update(data)
        it = self.selection.get_selected()[1]
        if it is None:
            self.selection.select_path(0)
        if not main_widget_found and main_widget:
            self.main_box.remove(main_widget)

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

    def about(self, *args):
        about = gtk.AboutDialog()
        about.set_name("Gll")
        about.set_comments("A graphical user interface for microlensing "
                           "computations based on the Lucky Lensing Library")
        about.set_copyright(u"© Sven Marnach, 2010")
        about.run()
        about.destroy()

    def quit_app(self, *args):
        self.cancel_pipeline()
        gtk.main_quit()

gobject.threads_init()
app = GllApp()
gtk.main()

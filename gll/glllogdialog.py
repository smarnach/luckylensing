from processor import logger, stdout_handler
import logging
import logging.handlers
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from cStringIO import StringIO
import gtk
import gobject

class GllBufferingHandler(logging.handlers.BufferingHandler):
    def flush(self):
        del self.buffer[:self.capacity/4]

    def flush_all(self):
        self.buffer = []

    def query(self, target, lvl):
        for record in self.buffer:
            if record.levelno >= lvl:
                target.handle(record)

buf_handler = GllBufferingHandler(256)
logger.addHandler(buf_handler)
stdout_handler.setLevel(CRITICAL)

class GllLogDialog(gtk.Dialog):
    def __init__(self, level=None, txt=""):
        gtk.Dialog.__init__(self, "Pipeline log", None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        if level is None:
            level = INFO
        self.level = level
        self.all_levels = [DEBUG, INFO, WARNING, ERROR]
        label = gtk.Label(txt)
        label.set_alignment(0.0, 0.5)
        label2 = gtk.Label("Display level for log messages: ")
        combobox = gtk.combo_box_new_text()
        for lvl in self.all_levels:
            combobox.append_text(logging.getLevelName(lvl))
        combobox.set_active(self.all_levels.index(self.level))
        combobox.connect("changed", self.level_changed)
        hbox = gtk.HBox()
        hbox.pack_start(label2, False)
        hbox.pack_start(combobox, False)
        self.buffer = gtk.TextBuffer()
        self.textview = gtk.TextView(self.buffer)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_size_request(500, 300)
        scrolledwindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolledwindow.add(self.textview)
        vbox = gtk.VBox()
        vbox.set_spacing(10)
        vbox.set_border_width(10)
        vbox.pack_start(label)
        vbox.pack_start(scrolledwindow)
        vbox.pack_start(hbox, False)
        vbox.show_all()
        self.vbox.pack_start(vbox)
        button = gtk.Button(stock=gtk.STOCK_CLEAR)
        button.connect("clicked", self.clear_log)
        button.show()
        self.action_area.pack_start(button)
        self.action_area.reorder_child(button, 0)
        self.query_log()

    def query_log(self):
        buf = StringIO()
        handler = logging.StreamHandler(buf)
        buf_handler.query(handler, self.level)
        self.buffer.set_text(buf.getvalue())
        def scroll_to_end():
            self.textview.scroll_to_iter(self.buffer.get_end_iter(), 0.0)
        gobject.idle_add(scroll_to_end)

    def level_changed(self, combobox):
        self.level = self.all_levels[combobox.get_active()]
        self.query_log()

    def clear_log(self, *args):
        buf_handler.flush_all()
        self.buffer.set_text("")

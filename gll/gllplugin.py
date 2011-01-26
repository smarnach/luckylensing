# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import gobject

class GllPlugin(gobject.GObject):
    __gsignals__ = {
        "run-pipeline": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "cancel-pipeline": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "statusbar-push": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,)),
        "statusbar-pop": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "history-back": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "history-forward": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())}

    name = "Gll plug-in"

    def __init__(self, processor=None):
        super(GllPlugin, self).__init__()
        self.processor = processor
        self.main_widget = None
        self.config_widget = None
        self.history = {}

    def update_config(self, data, data_serials, serial, last_serial):
        config = self.get_config()
        history_entry = self.history.get(last_serial)
        if history_entry is not None:
            last_config, last_serials = history_entry
            config_serials = {}
            for key in config:
                if config[key] == last_config.get(key):
                    config_serials[key] = last_serials[key]
                else:
                    config_serials[key] = serial
        else:
            config_serials = dict.fromkeys(config, serial)
        self.history[serial] = config, config_serials
        data.update(config)
        data_serials.update(config_serials)

    def restore_config(self, data, serial):
        config = self.history[serial][0]
        self.set_config(config)
        data.update(config)

    def restrict_history(self, serials):
        self.history = dict((s, self.history[s])
                            for s in serials if s in self.history)

    def get_config(self):
        if self.config_widget is not None:
            return self.config_widget.get_config()
        return {}

    def set_config(self, config):
        if self.config_widget is not None:
            self.config_widget.set_config(config)

    def update(self, data):
        pass

    def get_actions(self):
        return []

gobject.type_register(GllPlugin)

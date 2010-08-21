import gobject

class GllPlugin(gobject.GObject):
    __gsignals__ = {
        "run-pipeline": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "cancel-pipeline": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "history-back": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "history-forward": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())}

    def __init__(self):
        super(GllPlugin, self).__init__()
        self.processor = None
        self.main_widget = None
        self.config_widget = None

    def get_config(self):
        return {}

    def set_config(self, config):
        pass

    def update(self, data):
        pass

gobject.type_register(GllPlugin)

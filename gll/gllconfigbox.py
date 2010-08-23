import gtk

class GllConfigBox(gtk.VBox):
    def __init__(self, config_items):
        super(GllConfigBox, self).__init__(spacing=4)
        self.adjustments = {}
        for item in config_items:
            if not isinstance(item, gtk.Widget):
                key, text, adj_args, digits = item
                label = gtk.Label(text)
                label.set_width_chars(18)
                label.set_alignment(0.0, 0.5)
                adjustment = gtk.Adjustment(*adj_args)
                spinbutton = gtk.SpinButton(adjustment, digits=digits)
                item = gtk.HBox()
                item.pack_start(label, False, False)
                item.pack_start(spinbutton, True, True)
                self.adjustments[key] = adjustment
            self.pack_start(item, False, False)
        self.set_border_width(4)
        self.show_all()

    def __getitem__(self, index):
        return self.get_children()[index]

    def get_config(self):
        return dict((key, self.adjustments[key].get_value())
                    for key in self.adjustments)

    def set_config(self, config):
        for key in self.adjustments:
            self.adjustments[key].set_value(config[key])

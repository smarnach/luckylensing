import gtk

class GllConfigBox(gtk.VBox):
    def __init__(self, config_items=None):
        super(GllConfigBox, self).__init__(spacing=4)
        self.set_border_width(4)
        self.adjustments = {}
        self.toggle_blocks = {}
        self.ints = []
        self.sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        if config_items is not None:
            self.add_items(config_items)

    def add_items(self, config_items, block_key=None):
        for item in config_items:
            if not isinstance(item, gtk.Widget):
                key, text, adj_args, digits = item
                label = gtk.Label(text)
                label.set_width_chars(18)
                label.set_alignment(0.0, 0.5)
                adjustment = gtk.Adjustment(*adj_args)
                spinbutton = gtk.SpinButton(adjustment, digits=digits)
                item = gtk.HBox()
                item.pack_start(label, False)
                item.pack_start(spinbutton)
                if block_key is not None:
                    self.toggle_blocks[block_key][2][key] = adjustment
                else:
                    self.adjustments[key] = adjustment
                if not digits:
                    self.ints.append(key)
            if block_key is not None:
                self.toggle_blocks[block_key][1].append(item)
            self.pack_start(item, False)
            if isinstance(item, gtk.HBox):
                self.sizegroup.add_widget(item.get_children()[0])
        self.show_all()

    def add_toggle_block(self, key, text, active, config_items):
        checkbutton = gtk.CheckButton(text)
        checkbutton.set_active(active)
        checkbutton.connect("toggled", self.block_toggled, key)
        self.pack_start(checkbutton, False)
        self.toggle_blocks[key] = (checkbutton, [], {})
        self.add_items(config_items, key)
        self.block_toggled(checkbutton, key)

    def get_config(self):
        config = dict((key, self.adjustments[key].get_value())
                      for key in self.adjustments)
        for block_key, block in self.toggle_blocks.iteritems():
            checkbutton, widgets, adjustments = block
            state = checkbutton.get_active()
            config[block_key] = state
            if state:
                config.update((key, adjustments[key].get_value())
                              for key in adjustments)
        for key in self.ints:
            if key in config:
                config[key] = int(config[key])
        return config

    def set_config(self, config):
        for key in self.adjustments:
            self.adjustments[key].set_value(config[key])
        for block_key, block in self.toggle_blocks.iteritems():
            checkbutton, widgets, adjustments = block
            state = config[block_key]
            checkbutton.set_active(state)
            if state:
                for key in adjustments:
                    adjustments[key].set_value(config[key])

    def set_value(self, key, value):
        if key in self.adjustments:
            self.adjustments[key].set_value(value)
            return
        for block_key, block in self.toggle_blocks.iteritems():
            checkbutton, widgets, adjustments = block
            if key in adjustments:
                adjustments[key].set_value(value)
                return
        raise KeyError(key)

    def set_active(self, key, active):
        self.toggle_blocks[key][0].set_active(active)

    def block_toggled(self, checkbutton, block_key):
        state = checkbutton.get_active()
        for widget in self.toggle_blocks[block_key][1]:
            widget.set_sensitive(state)

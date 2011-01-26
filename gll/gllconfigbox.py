# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

import gtk

class GllConfigAdjustment(gtk.HBox):
    def __init__(self, text, adj_args, digits):
        gtk.HBox.__init__(self)
        label = gtk.Label(text)
        label.set_width_chars(18)
        label.set_alignment(0.0, 0.5)
        self.adjustment = gtk.Adjustment(*adj_args)
        spinbutton = gtk.SpinButton(self.adjustment, digits=digits)
        self.pack_start(label, False)
        self.pack_start(spinbutton)
        self.isint = (digits == 0)

    def get_value(self):
        value = self.adjustment.get_value()
        if self.isint:
            return int(value)
        return value

    def set_value(self, value):
        self.adjustment.set_value(value)

class GllConfigCheckButton(gtk.CheckButton):
    get_value = gtk.CheckButton.get_active
    set_value = gtk.CheckButton.set_active

class GllConfigRadioButtons(gtk.HBox):
    def __init__(self, label_text, start_value, choices):
        gtk.HBox.__init__(self)
        label = gtk.Label(label_text)
        label.set_alignment(0.0, 0.0)
        label.set_padding(0, 4)
        self.pack_start(label, False)
        self.choices = {}
        firstbutton = None
        buttonbox = gtk.VBox()
        for text, value in choices:
            radiobutton = gtk.RadioButton(firstbutton, text)
            buttonbox.pack_start(radiobutton)
            self.choices[value] = radiobutton
            firstbutton = firstbutton or radiobutton
        self.pack_start(buttonbox)
        self.set_value(start_value)

    def get_value(self):
        for value, radiobutton in self.choices.iteritems():
            if radiobutton.get_active():
                return value

    def set_value(self, value):
        self.choices[value].set_active(True)

class GllConfigGroup(gtk.VBox):
    def __init__(self, sizegroup, config_items=None):
        gtk.VBox.__init__(self, spacing=4)
        self.sizegroup = sizegroup
        self.items = {}
        self.subgroups = []
        if config_items is not None:
            self.add_items(config_items)

    def __getitem__(self, key):
        if key in self.items:
            return self.items[key]
        for group in self.subgroups:
            try:
                return group[key]
            except KeyError:
                pass
        raise KeyError(key)

    def __contains__(self, key):
        if key in self.items:
            return True
        return any(key in group for group in self.subgroups)

    def add_items(self, item):
        if isinstance(item, list):
            for i in item:
                self.add_items(i)
            return
        if isinstance(item, tuple):
            key = item[0]
            if len(item) > 2:
                item = GllConfigAdjustment(*item[1:])
            else:
                item = item[1]
            self.items[key] = item
        elif isinstance(item, GllConfigGroup):
            self.subgroups.append(item)
        if isinstance(item, gtk.HBox):
            self.sizegroup.add_widget(item.get_children()[0])
        self.pack_start(item, False)
        self.show_all()

    def get_config(self):
        config = dict((key, self.items[key].get_value()) for key in self.items)
        for group in self.subgroups:
            config.update(group.get_config())
        return config

    def set_config(self, config):
        for key in self.items:
            self.items[key].set_value(config[key])
        for group in self.subgroups:
            group.set_config(config)

class GllConfigToggleGroup(GllConfigGroup):
    def __init__(self, sizegroup, key, text, active, config_items):
        GllConfigGroup.__init__(self, sizegroup)
        checkbutton = GllConfigCheckButton(text)
        checkbutton.connect("toggled", self.toggled)
        self.pack_start(checkbutton, False)
        self.items[key] = checkbutton
        self.key = key
        self.add_items(config_items)
        checkbutton.set_active(active)

    def get_config(self):
        state = self.items[self.key].get_active()
        if state:
            return GllConfigGroup.get_config(self)
        else:
            return {self.key: state}

    def set_config(self, config):
        state = config[self.key]
        if state:
            GllConfigGroup.set_config(self, config)
        else:
            self.items[self.key].set_active(state)

    def toggled(self, checkbutton):
        state = checkbutton.get_active()
        for key in self.items:
            if key != self.key:
                self.items[key].set_sensitive(state)
        for group in self.subgroups:
            group.set_sensitive(state)

class GllConfigBox(GllConfigGroup):
    def __init__(self, config_items=None):
        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        GllConfigGroup.__init__(self, sizegroup, config_items)
        self.set_border_width(4)

    def add_toggle_group(self, *args):
        self.add_items(GllConfigToggleGroup(self.sizegroup, *args))

    def add_radio_buttons(self, key, *args):
        self.add_items((key, GllConfigRadioButtons(*args)))

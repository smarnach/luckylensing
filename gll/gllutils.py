import gtk

def add_file_filters(filechooser, filter_specs):
    filters = []
    for name, pattern in [("All files", "*")] + filter_specs:
        filt = gtk.FileFilter()
        if pattern != "*":
            filt.set_name(name + " (" + pattern + ")")
        else:
            filt.set_name(name)
        filt.add_pattern(pattern)
        filters.append(filt)
        filechooser.add_filter(filt)
    if filter_specs:
        filechooser.set_filter(filters[1])

def open_save_dialog(action, title, filter_specs):
    if action == gtk.FILE_CHOOSER_ACTION_OPEN:
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                   gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT)
    elif action == gtk.FILE_CHOOSER_ACTION_SAVE:
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                   gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT)
    dialog = gtk.FileChooserDialog(title, action=action, buttons=buttons)
    dialog.set_do_overwrite_confirmation(True)
    add_file_filters(dialog, filter_specs)
    response = dialog.run()
    filename = dialog.get_filename()
    dialog.destroy()
    if response == gtk.RESPONSE_ACCEPT:
        return filename
    else:
        return None

def open_dialog(title, filter_specs = []):
    return open_save_dialog(gtk.FILE_CHOOSER_ACTION_OPEN, title, filter_specs)

def save_dialog(title, filter_specs = []):
    return open_save_dialog(gtk.FILE_CHOOSER_ACTION_SAVE, title, filter_specs)

class Processor(object):
    def __init__(self):
        super(Processor, self).__init__()
        self.history = {}
        self.last_serial = -1

    def get_input_keys(self, data):
        raise NotImplementedError

    def needs_update(self, data, data_serials):
        history_entry = self.history.get(self.last_serial)
        if history_entry:
            last_serials = history_entry[1]
            for key in data_serials:
                if data_serials.get(key) != last_serials.get(key):
                    return True
            return False
        return True

    def update(self, data, data_serials=None, serial=None):
        if data_serials is None:
            data.update(self.run(data))
            return
        my_serials = dict((key, data_serials[key])
                          for key in self.get_input_keys(data)
                          if key in data_serials)
        if self.needs_update(data, my_serials):
            output = self.run(data)
            self.last_serial = serial
        else:
            output = self.history[self.last_serial][0]
        self.history[serial] = output, my_serials
        data.update(output)
        data_serials.update(dict.fromkeys(output, self.last_serial))

    def restore(self, data, serial):
        data.update(self.history[serial][0])
        self.last_serial = serial

    def restrict_history(self, serials):
        self.history = dict((s, self.history[s])
                            for s in serials if s in self.history)

    def run(self, data):
        return {}

    def cancel(self):
        pass

    def get_progress(self):
        return 1.0

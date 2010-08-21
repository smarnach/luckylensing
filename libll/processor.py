class Processor(object):
    def __init__(self):
        super(Processor, self).__init__()
        self.history = {}
        self.serials = {}
        self.last_serial = -1

    def get_input_keys(self, data):
        raise NotImplementedError

    def needs_update(self, data, data_serials):
        newest_input = 0
        for key in self.get_input_keys(data):
            if key in data and data_serials[key] > newest_input:
                newest_input = data_serials[key]
        return self.last_serial < newest_input

    def update(self, data, data_serials=None, serial=None):
        if data_serials is None:
            data.update(self.run(data))
            return
        if self.needs_update(data, data_serials):
            output = self.run(data)
            self.last_serial = serial
        else:
            output = self.history[self.last_serial]
        self.history[serial] = output
        self.serials[serial] = self.last_serial
        data.update(output)
        data_serials.update(dict.fromkeys(output, self.last_serial))

    def restore(self, data, serial):
        data.update(self.history[serial])
        self.last_serial = self.serials[serial]

    def restrict_history(self, serials):
        self.history = dict((s, self.history[s])
                            for s in serials if s in self.history)
        self.serials = dict((s, self.serials[s])
                            for s in serials if s in self.serials)

    def run(self, data):
        return {}

    def cancel(self):
        pass

    def get_progress(self):
        return 1.0

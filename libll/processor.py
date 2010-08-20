class Processor(object):
    def __init__(self):
        super(Processor, self).__init__()
        self.history = []

    def get_input_keys(self, data):
        raise NotImplementedError

    def needs_update(self, data, data_serials, cached_serial):
        newest_input = -1
        for key in self.get_input_keys(data):
            if key in data and data_serials[key] > newest_input:
                newest_input = data_serials[key]
        return cached_serial < newest_input

    def update(self, data, data_serials=None, serial=None):
        if data_serials is None:
            data.update(self.run(data))
            return
        if (not self.history or
            self.needs_update(data, data_serials, self.history[-1][0])):
            out_serial, output = serial, self.run(data)
            self.history.append((out_serial, output))
        else:
            out_serial, output = self.history[-1]
        data.update(output)
        data_serials.update(dict.fromkeys(output, out_serial))

    def run(self, data):
        return {}

    def cancel(self):
        pass

    def get_progress(self):
        return 1.0

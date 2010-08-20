class Processor(object):
    def get_input_keys(self, data):
        return [] # names of used data

    def get_output_keys(self, data):
        return [] # names of generated outputs

    def run(self, data):
        return {} # outputs

    def cancel(self):
        pass

    def get_progress(self):
        return 1.0

class Pipeline(list):
    def run(self, data = None):
        if data is None:
            data = {}
        for proc in self:
            outputs = proc.run(data)
            data.update(outputs)
        return data

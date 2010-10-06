import logging
import sys
import time
from itertools import chain

logger = logging.getLogger("luckylensing")
logger.setLevel(logging.DEBUG)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

class ProcessorInterface(object):
    def get_input_keys(self, data):
        raise NotImplementedError

    def run(self, data):
        return {}

    def cancel(self):
        pass

    def get_progress(self):
        return 1.0

class Processor(ProcessorInterface):
    def __init__(self):
        super(Processor, self).__init__()
        self.history = {}
        self.last_serial = -1

    def run_and_log(self, data):
        name = self.__class__.__name__
        logger.debug("Starting %s", name)
        wall_time = time.time()
        cpu_time = time.clock()
        output = self.run(data)
        wall_time = time.time() - wall_time
        cpu_time = time.clock() - cpu_time
        if wall_time >= 0.1:
            level = logging.INFO
        else:
            level = logging.DEBUG
        logger.log(level, "Finished %s in %.2f s (wall time), "
                   "%.2f s (CPU time)", name, wall_time, cpu_time)
        return output

    def needs_update(self, data, data_serials):
        history_entry = self.history.get(self.last_serial)
        if history_entry is None:
            return True
        last_serials = history_entry[1]
        return any(data_serials.get(key) != last_serials.get(key)
                   for key in chain(data_serials, last_serials))

    def update(self, data, data_serials=None, serial=None):
        if data_serials is None:
            data.update(self.run_and_log(data))
            return
        my_serials = dict((key, data_serials[key])
                          for key in self.get_input_keys(data)
                          if key in data_serials)
        if self.needs_update(data, my_serials):
            output = self.run_and_log(data)
            self.last_serial = serial
        else:
            logger.debug("Reusing %s result of run #%i",
                         self.__class__.__name__, self.last_serial)
            output = self.history[self.last_serial][0]
        self.history[serial] = output, my_serials, self.last_serial
        data.update(output)
        data_serials.update(dict.fromkeys(output, self.last_serial))

    def restore(self, data, serial):
        data.update(self.history[serial][0])
        self.last_serial = self.history[serial][2]

    def restrict_history(self, serials):
        self.history = dict((s, self.history[s])
                            for s in serials if s in self.history)

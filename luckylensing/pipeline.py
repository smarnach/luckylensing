# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from __future__ import division, absolute_import
try:
    from itertools import imap as map
except ImportError:
    pass
from . import utils
import logging
import time
import itertools
import inspect

try:
    import resource
    def clock():
        return sum(resource.getrusage(resource.RUSAGE_SELF)[:2])
except ImportError:
    clock = time.clock

class Processor(object):

    def __init__(self, action):
        self.history = {}
        self.last_serial = -1
        self.name = action.__name__
        if inspect.isclass(action):
            self.inputs = set(inspect.getargspec(action.__init__)[0])
            self.inputs.remove("self")
            self.action = self._class_action
            self.action_class = action
        else:
            self.inputs = set(inspect.getargspec(action)[0])
            self.action = action

    def _class_action(self, **kwargs):
        action = self.action_class(**kwargs)
        self.cancel = action.cancel
        self.get_progress = action.get_progress
        result = action.run()
        del self.cancel, self.get_progress
        return result

    def cancel(self):
        pass

    def get_progress(self):
        return 1.0

    def run_and_log(self, data):
        utils.logger.debug("Starting %s", self.name)
        wall_time = time.time()
        cpu_time = clock()
        try:
            data_items = data.iteritems()
        except AttributeError:
            data_items = data.items()
        kwargs = dict((k, v) for k, v in data_items if k in self.inputs)
        output = self.action(**kwargs)
        wall_time = time.time() - wall_time
        cpu_time = clock() - cpu_time
        if wall_time >= 0.1:
            level = logging.INFO
        else:
            level = logging.DEBUG
        utils.logger.log(level, "Finished %s in %.2f s (wall time), "
                         "%.2f s (CPU time)", self.name, wall_time, cpu_time)
        if isinstance(output, dict):
            return output
        if output is None:
            output = ()
        if not isinstance(output, tuple):
            output = output,
        return dict((v.arg_name, v) for v in output)

    def needs_update(self, data, data_serials):
        history_entry = self.history.get(self.last_serial)
        if history_entry is None:
            return True
        last_serials = history_entry[1]
        return any(data_serials.get(key) != last_serials.get(key)
                   for key in itertools.chain(data_serials, last_serials))

    def update(self, data, data_serials=None, serial=None):
        if data_serials is None:
            data.update(self.run_and_log(data))
            return
        my_serials = dict((key, data_serials[key])
                          for key in self.inputs if key in data_serials)
        if self.needs_update(data, my_serials):
            output = self.run_and_log(data)
            self.last_serial = serial
        else:
            utils.logger.debug("Reusing %s result of run #%i",
                               self.name, self.last_serial)
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

class Pipeline(object):
    def __init__(self, *actions):
        self.processors = list(map(Processor, actions))
    def run(self, data=None, **kwargs):
        if data is None:
            data = kwargs
        for processor in self.processors:
            processor.update(data)

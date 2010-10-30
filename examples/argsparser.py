# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from luckylensing import Processor

class ArgsParser(Processor):
    def get_input_keys(self, data):
        return ["args"]

    def run(self, data):
        output = {}
        for arg in data["args"]:
            key, value = arg.split("=", 1)
            if key.startswith("--"):
                key = key[2:]
            if value.startswith("eval(") and value.endswith(")"):
                value = eval(value[5:-1])
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            output[key.replace("-", "_")] = value
        return output

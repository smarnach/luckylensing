from processor import Processor

class ArgsParser(Processor):
    def get_input_keys(self, data):
        return ["args"]

    def run(self, data):
        output = {}
        for arg in data["args"]:
            key, value = arg.split("=", 1)
            if len(key) >= 2 and key[:2] == "--":
                key = key[2:]
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
            output[key.replace("-", "_")] = value
        return output

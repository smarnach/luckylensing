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
            if len(value) > 6 and value[:5] == "expr(" and value[-1:] == ")":
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

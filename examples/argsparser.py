# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

def parse_args(args):
    output = {}
    for arg in args:
        key, value = arg.split("=", 1)
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

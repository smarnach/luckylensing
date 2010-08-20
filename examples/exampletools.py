from subprocess import Popen, PIPE
from os import unlink

colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
          (195, 16, 16), (249, 249, 70), (255, 255, 255)]
steps = [255, 32, 255, 255, 255]

def save_png(buf, filename):
    size = "%ix%i" % (buf.shape[1], buf.shape[0])
    p = Popen(["convert", "-size", size, "-depth", "8", "rgb:-", filename],
              stdin=PIPE)
    buf.tofile(p.stdin)
    p.stdin.close()
    p.wait()

def get_ints_from_files(args):
    delete =  (args[0] == "--delete")
    if delete:
        del args[0]
    for f in args:
        try:
            lines = open(f).readlines()
            ints = map(int, lines)
            if delete:
                unlink(f)
        except (IOError, OSError):
            continue
        for i in ints:
            yield i

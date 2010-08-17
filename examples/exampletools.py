from subprocess import Popen, PIPE

colors = [(0, 0, 0), (0, 0, 255), (32, 0, 255),
          (255, 0, 0), (255, 255, 0), (255, 255, 255)]
steps = [255, 32, 255, 255, 255]

def save_png(buf, filename):
    size = "%ix%i" % (buf.shape[1], buf.shape[0])
    p = Popen(["convert", "-size", size, "-depth", "8", "rgb:-", filename],
              stdin=PIPE)
    buf.tofile(p.stdin)
    p.stdin.close()
    p.wait()

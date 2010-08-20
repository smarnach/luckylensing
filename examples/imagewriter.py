import sys
sys.path.append("../libll")

from subprocess import Popen, PIPE
from processor import Processor
from luckylensing import render_magpattern_gradient

colors = [(0, 0, 0), (5, 5, 184), (29, 7, 186),
          (195, 16, 16), (249, 249, 70), (255, 255, 255)]
steps = [255, 32, 255, 255, 255]

def save_img(buf, filename, convert_opts=""):
    size = "%ix%i" % (buf.shape[1], buf.shape[0])
    p = Popen(["convert", "-size", size, "-depth", "8", "rgb:-"]
              + convert_opts.split() + [filename], stdin=PIPE)
    buf.tofile(p.stdin)
    p.stdin.close()
    p.wait()

class ImageWriter(Processor):
    def get_input_keys(self, data):
        return ["magpat", "min_mag", "max_mag", "imgfile", "convert_opts"]

    def run(self, data):
        imgfile = data.get("imgfile")
        if not imgfile:
            return {}
        min_mag = data.get("min_mag")
        max_mag = data.get("max_mag")
        buf = render_magpattern_gradient(data["magpat"], colors, steps,
                                         min_mag, max_mag)
        save_img(buf, imgfile, data.get("convert_opts", ""))
        return {}

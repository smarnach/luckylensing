import sys
sys.path.append("../libll")

from math import sqrt, log, ceil
from time import time
import threading
from Queue import Queue, Empty
import numpy
import luckylensing as ll

class Rayshooter(ll.BasicRayshooter):
    def __init__(self, params):
        super(Rayshooter, self).__init__(params)
        self.density = 100
        self.count = None
        self.progress = []

    def get_progress(self):
        return sum(p.value for p in self.progress)

    def get_shooting_params(self):
        """Determine ray shooter parameters for given self.density

        This function returns a tuple (rect, xrays, yrays, levels)
        which can be used as parameters for an Rayshooter instance.
        The parameters guarantee a large enough shooting rectangle to
        complety cover all rays hitting the magnification pattern.
        The ray density for magnification 1 is exactly self.density
        rays per pixel, with equal horizontal and vertical densities.
        """
        params = self.params[0]
        lens = [params.lenses.lens[i] for i in range(params.lenses.num_lenses)]
        rect = ll.Rect()
        x0 = min(l.x - sqrt(l.mass) for l in lens)
        d = sum(l.mass/(x0 - l.x) for l in lens)
        rect.x = min(x0, params.region.x + d)
        y0 = min(l.y - sqrt(l.mass) for l in lens)
        d = sum(l.mass/(y0 - l.y) for l in lens)
        rect.y = min(y0, params.region.y + d)
        x1 = max(l.x + sqrt(l.mass) for l in lens)
        d = sum(l.mass/(x1 - l.x) for l in lens)
        rect.width = max(x1, params.region.x + params.region.width + d) - rect.x
        y1 = max(l.y + sqrt(l.mass) for l in lens)
        d = sum(l.mass/(y1 - l.y) for l in lens)
        rect.height = max(y1, params.region.y + params.region.height + d) - rect.y

        # Determine number of rays needed to achieve the ray density
        # specified by self.density (assuming magnification = 1)
        rays = sqrt(self.density) / self.refine_final
        xraysf = rays * params.xpixels * rect.width / params.region.width
        yraysf = rays * params.ypixels * rect.height / params.region.height
        levels = max(0, int(log(min(xraysf, yraysf)/50)/log(self.refine)))
        xraysf /= self.refine**levels
        yraysf /= self.refine**levels
        xrays = int(ceil(xraysf))
        yrays = int(ceil(yraysf))
        rect.width *= xrays/xraysf
        rect.height *= yrays/yraysf

        return rect, xrays, yrays, levels + 2

    def start(self, num_threads=2):
        self.cancel_flag = False
        shape = self.params[0].ypixels, self.params[0].xpixels
        self.count = numpy.zeros(shape, numpy.float32)
        rect, xrays, yrays, levels = self.get_shooting_params()
        print xrays, yrays
        print levels

        start_time = time()
        hit = numpy.empty((yrays, xrays), numpy.uint8)
        y_indices = [j*yrays//num_threads for j in range(num_threads + 1)]
        y_values =  [rect.y + j*(rect.height/yrays) for j in y_indices]
        subpatches = []
        for j in range(num_threads):
            subrect = ll.Rect(rect.x, y_values[j], rect.width,
                              y_values[j+1] - y_values[j])
            subhit = hit[y_indices[j]:y_indices[j+1]]
            subpatches.append(ll.Patches(subrect, levels - 1, subhit))
        threads = [threading.Thread(target=self.get_subpatches,
                                    args=(subpatches[j],))
                   for j in range(1, num_threads)]
        for t in threads:
            t.start()
        self.get_subpatches(subpatches[0])
        counts = [self.count] + [numpy.zeros_like(self.count)
                                 for j in range(num_threads)]
        patches = ll.Patches(rect, levels - 1, hit)
        for t in threads:
            t.join()
        patches.num_patches = sum(p.num_patches for p in subpatches)
        self.progress = [ll.Progress(0.0) for j in range(num_threads)]
        subdomains = self.refine
        x_indices = [i*xrays//subdomains for i in range(subdomains + 1)]
        x_values =  [rect.x + i*(rect.width/xrays) for i in x_indices]
        y_indices = [j*yrays//subdomains for j in range(subdomains + 1)]
        y_values =  [rect.y + j*(rect.height/yrays) for j in y_indices]
        queue = Queue()
        for j in range(subdomains):
            for i in range(subdomains):
                subrect = ll.Rect(x_values[i], y_values[j],
                                  x_values[i+1] - x_values[i],
                                  y_values[j+1] - y_values[j])
                queue.put((subrect, x_indices[i], x_indices[i+1],
                           y_indices[j], y_indices[j+1]))
        threads = [threading.Thread(target=self._start_queue,
                                    args=(queue, counts[j], patches, hit, j))
                   for j in range(1, num_threads)]
        for t in threads:
            t.start()
        self._start_queue(queue, counts[0], patches, hit, 0)
        for t in threads:
            t.join()
        for c in counts[1:]:
            self.count += c
        print time()-start_time
        self.progress = []

    def _start_queue(self, queue, count, patches, hit, index):
        try:
            while True:
                rect, i0, i1, j0, j1 = queue.get(False)
                subhit = numpy.ascontiguousarray(hit[j0:j1, i0:i1])
                subpatches = ll.Patches(rect, patches.level, subhit)
                subpatches.num_patches = patches.num_patches
                self.start_subpatches(count, subpatches, self.progress[index])
        except Empty:
            self.finalise_subpatches(count, patches)

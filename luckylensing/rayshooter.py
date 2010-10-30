# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from math import sqrt, log, ceil
import threading
from Queue import Queue, Empty
import numpy
import libll as ll
from processor import Processor, logger

class Rayshooter(ll.BasicRayshooter, Processor):
    def __init__(self, params=None):
        ll.BasicRayshooter.__init__(self, params)
        Processor.__init__(self)
        self.density = 100
        self.num_threads = 1
        self.magpat = None
        self.progress = []

    def get_input_keys(self, data):
        return ["lenses", "region_x0", "region_x1", "region_y0", "region_y1",
                "xpixels", "ypixels", "kernel", "refine", "refine_final",
                "density", "num_threads"]

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
        if lens:
            rect = ll.Rect()
            x0 = min(l.x - sqrt(l.mass) for l in lens)
            d = sum(l.mass/(x0 - l.x) for l in lens)
            rect.x = min(x0, params.region.x + d)
            y0 = min(l.y - sqrt(l.mass) for l in lens)
            d = sum(l.mass/(y0 - l.y) for l in lens)
            rect.y = min(y0, params.region.y + d)
            x1 = max(l.x + sqrt(l.mass) for l in lens)
            d = sum(l.mass/(x1 - l.x) for l in lens)
            rect.width = max(x1, params.region.x +
                             params.region.width + d) - rect.x
            y1 = max(l.y + sqrt(l.mass) for l in lens)
            d = sum(l.mass/(y1 - l.y) for l in lens)
            rect.height = max(y1, params.region.y +
                              params.region.height + d) - rect.y
        else:
            rect = ll.Rect(params.region.x, params.region.y,
                           params.region.width, params.region.height)

        # Determine number of rays needed to achieve the ray density
        # specified by self.density (assuming magnification = 1)
        rays = sqrt(self.density) / self.refine_final
        xraysf = rays * params.xpixels * rect.width / params.region.width
        yraysf = rays * params.ypixels * rect.height / params.region.height
        levels = max(1, int(log(min(xraysf, yraysf)/75)/log(self.refine)))
        xraysf /= self.refine**levels
        yraysf /= self.refine**levels
        xrays = int(ceil(xraysf))
        yrays = int(ceil(yraysf))
        rect.width *= xrays/xraysf
        rect.height *= yrays/yraysf

        return rect, xrays, yrays, levels + 2

    def run(self, data=None):
        if data:
            region = (data["region_x0"], data["region_y0"],
                      data["region_x1"] - data["region_x0"],
                      data["region_y1"] - data["region_y0"])
            xpixels = data.get("xpixels", 1024)
            ypixels = data.get("ypixels", 1024)
            self.params[0] = ll.MagPatternParams(data["lenses"], region,
                                                 xpixels, ypixels)
            for key in ["refine", "refine_final", "density", "num_threads"]:
                if key in data:
                    setattr(self, key, data[key])
            if "kernel" in data:
                kernel = data["kernel"]
                if isinstance(kernel, str):
                    if "simple" in kernel.lower():
                        self.kernel = ll.KERNEL_SIMPLE
                    elif "bilinear" in kernel.lower():
                        self.kernel = ll.KERNEL_BILINEAR
                    elif "triangulated" in kernel.lower():
                        self.kernel = ll.KERNEL_TRIANGULATED
                    else:
                        raise ValueError("Cannot parse kernel: " + kernel)
                else:
                    self.kernel = kernel
        self.cancel_flag = False
        shape = self.params[0].ypixels, self.params[0].xpixels
        self.magpat = numpy.zeros(shape, numpy.float32)
        rect, xrays, yrays, levels = self.get_shooting_params()
        logger.debug("Ray shooting rectangle: %s", rect)
        logger.debug("Rays on the coarsest level: %i x %i", xrays, yrays)
        logger.debug("Ray shooting levels: %i", levels)
        self.progress = [ll.Progress(0.0) for j in range(self.num_threads)]
        if self.num_threads > 1:
            self._run_threaded(rect, xrays, yrays, levels)
        else:
            ll.BasicRayshooter.run(self, self.magpat, rect, xrays, yrays,
                                   levels, progress=self.progress[0])
        self.progress = []
        if data:
            return {"shooting_rect": rect, "xrays": xrays, "yrays": yrays,
                    "levels": levels, "magpat": self.magpat}

    def _run_threaded(self, rect, xrays, yrays, levels):
        num_threads = self.num_threads
        patches = ll.Patches(rect, levels - 1, xrays, yrays)
        y_indices = [j*yrays//num_threads for j in range(num_threads + 1)]
        y_values =  [rect.y + j*(rect.height/yrays) for j in y_indices]
        subpatches = []
        for j in range(num_threads):
            subrect = ll.Rect(rect.x, y_values[j], rect.width,
                              y_values[j+1] - y_values[j])
            subhit = patches.hit_array[y_indices[j]:y_indices[j+1]]
            subpatches.append(ll.Patches(subrect, levels - 1, hit=subhit))
        threads = [threading.Thread(target=self.get_subpatches,
                                    args=(subpatches[j],))
                   for j in range(1, num_threads)]
        for t in threads:
            t.start()
        self.get_subpatches(subpatches[0])
        magpats = [self.magpat] + [numpy.zeros_like(self.magpat)
                                   for j in range(num_threads)]
        for t in threads:
            t.join()
        patches.num_patches = sum(p.num_patches for p in subpatches)
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
        threads = [threading.Thread(target=self._run_queue,
                                    args=(queue, magpats[j], patches, j))
                   for j in range(1, num_threads)]
        for t in threads:
            t.start()
        self._run_queue(queue, magpats[0], patches, 0)
        for t in threads:
            t.join()
        self.finalise_subpatches(magpats, patches)

    def _run_queue(self, queue, magpat, patches, index):
        hit = patches.hit_array
        try:
            while True:
                rect, i0, i1, j0, j1 = queue.get(False)
                subhit = numpy.ascontiguousarray(hit[j0:j1, i0:i1])
                subpatches = ll.Patches(rect, patches.level, hit=subhit)
                subpatches.num_patches = patches.num_patches
                self.run_subpatches(magpat, subpatches, self.progress[index])
        except Empty:
            pass

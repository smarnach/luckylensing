# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from __future__ import division
from math import sqrt, log, ceil
import threading
import Queue
import numpy
import libll
import utils
import lensconfig
import lightcurve

class Magpat(numpy.ndarray):

    """A magnification pattern.

    This class is basically a two-dimensional NumPy array of shape
    (ypixels, xpixels) -- note the order!

    Constructor:

        Magpat(xpixels, ypixels, lenses, region, buffer=None, offset=0)

        buffer and offset are passed on to numpy.ndarray.__new__().

    Instances have the following additional attributes:

        lenses           the associated LensConfig instance
        region           the coordinates of the source plane rectangle
                         occupied by this pattern
        params           a libll.MagpatParams instance encapsulating
                         xpixels, ypixels, lenses and region
    """

    arg_name = "magpat"

    def __new__(cls, xpixels, ypixels, lenses, region, buffer=None, offset=0):
        obj = numpy.ndarray.__new__(
            cls, (ypixels, xpixels), numpy.float32, buffer, offset)
        if not isinstance(lenses, lensconfig.LensConfig):
            lenses = lensconfig.LensConfig(lenses)
        if not isinstance(region, libll.Rect):
            try:
                region = utils.rectangle(**region)
            except TypeError:
                region = utils.rectangle(*region)
        obj.lenses = lenses
        obj.region = region
        obj.params = libll.MagpatParams(lenses, region, xpixels, ypixels)
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        for attr in ["lenses", "region", "params"]:
            setattr(self, attr, getattr(obj, attr, None))

    @classmethod
    def empty_like(cls, obj):
        """Create a new empty Magpat instance similar to obj.
        """
        ypixels, xpixels = obj.shape
        return Magpat.__new__(cls, xpixels, ypixels, obj.lenses, obj.region)

    def convolve(self, source_fft=None, source_radius=None,
                 profile_type="flat"):
        """Convolve the magnification pattern in place.

        If source_fft is given, it is passed on to convolve(),
        otherwise it is created using the source_profile() function
        with the given parameters.
        """
        if source_fft is None:
            source_fft = lightcurve.source_profile(
                self, source_radius, profile_type)[1]
        lightcurve.convolve(self, source_fft, self)

    def write_fits(self, fits_output_file):
        """Save the magnification pattern to a FITS file.

        The parameter fits_output_file is the file name of the FITS
        file, which will be overwritten.  If PyFITS is not available,
        an ImportError will be raised.
        """
        import fits
        fits.write_fits(self, fits_output_file)

    render_greyscale = libll.render_magpat_greyscale
    render_gradient = libll.render_magpat_gradient

class Rayshooter(object):

    """Control a multi-threaded ray shooter.

    Constructor:

        Rayshooter(lenses, region, xpixels=1024, ypixels=1024,
                   density=100, num_threads=1, kernel="triangulated",
                   refine=15, refine_kernel=25)

        lenses           a LensConfig instance or a list of triples
        region           a Rect instance or a tuple of coordinates
                         defining the source plane rectangle occupied
                         by the magnification pattern
        xpixels,         resolution of the magnification pattern
        ypixels
        density          ray density for shooting.  The number of rays
                         that hit a single pattern pixel will be
                             rays = density x avg_mag
                         where avg_mag is the average magnification of
                         the pixel.
        kernel           ray shooting kernel to use.  Possible values:
                             "simple"       -- Brute-force kernel
                             "bilinear"     -- Bilinear interpolation
                             "triangulated" -- Shoot triangles
        num_threads      number of ray shooting threads
        refine           factor by which to refine the shooting grid on
                         each level in x and y-direction
        refine_kernel    number of rays to use by the kernel in x and
                         y-direction; meaningless for "triangulated"
    """

    def __init__(self, lenses, region, xpixels=1024, ypixels=1024,
                 density=100, num_threads=1, kernel="triangulated",
                 refine=15, refine_kernel=25):
        self.magpat = Magpat(xpixels, ypixels, lenses, region)
        self.magpat.fill(0.0)
        self.density = density
        self.num_threads = num_threads
        self.rs = libll.BasicRayshooter(
            self.magpat.params, kernel, refine, refine_kernel)
        self.progress = []

    def get_progress(self):
        """Return the progress of the currently running ray shooting.
        """
        if not self.progress:
            return 1.0
        return sum(p.value for p in self.progress)

    def cancel(self):
        """Cancel the currently running ray shooting function.
        """
        self.rs.cancel()

    def run(self):
        """Actually shoot the rays and return the magnification pattern.

        The return value is a Magpat instance.
        """
        self.progress = [libll.Progress(0.0) for j in range(self.num_threads)]
        rect, xrays, yrays, levels = self.get_shooting_params()
        utils.logger.debug("Ray shooting rectangle: %s", rect)
        utils.logger.debug("Rays on the coarsest level: %i x %i", xrays, yrays)
        utils.logger.debug("Ray shooting levels: %i", levels)
        if self.num_threads > 1:
            self._run_threaded(rect, xrays, yrays, levels)
        else:
            self.rs.run(self.magpat, rect, xrays, yrays, levels,
                        progress=self.progress[0])
        self.progress = []
        return self.magpat

    def get_shooting_params(self):
        """Determine ray shooter parameters for given self.density

        This function returns a tuple (rect, xrays, yrays, levels)
        which can be used as parameters for an Rayshooter instance.
        The parameters guarantee a large enough shooting rectangle to
        complety cover all rays hitting the magnification pattern.
        The ray density for magnification 1 is exactly self.density
        rays per pixel, with equal horizontal and vertical densities.
        """
        lenses = self.magpat.lenses
        region = self.magpat.region
        if lenses.size:
            sqrt_mass = numpy.sqrt(lenses.mass)
            tmp = numpy.subtract(lenses.x, sqrt_mass)
            x0 = tmp.min()
            numpy.subtract(x0, lenses.x, tmp)
            numpy.divide(lenses.mass, tmp, tmp)
            x0 = min(x0, region.x0 + tmp.sum())
            tmp = numpy.subtract(lenses.y, sqrt_mass)
            y0 = tmp.min()
            numpy.subtract(y0, lenses.y, tmp)
            numpy.divide(lenses.mass, tmp, tmp)
            y0 = min(y0, region.y0 + tmp.sum())
            tmp = numpy.add(lenses.x, sqrt_mass)
            x1 = tmp.max()
            numpy.subtract(x1, lenses.x, tmp)
            numpy.divide(lenses.mass, tmp, tmp)
            x1 = max(x1, region.x1 + tmp.sum())
            tmp = numpy.add(lenses.y, sqrt_mass)
            y1 = tmp.max()
            numpy.subtract(y1, lenses.y, tmp)
            numpy.divide(lenses.mass, tmp, tmp)
            y1 = max(y1, region.y1 + tmp.sum())
            rect = utils.rectangle(x0, y0, x1, y1)
        else:
            rect = utils.rectangle(region.x0, region.y0, region.x1, region.y1)

        rays = sqrt(self.density) / self.rs.refine_kernel
        ypixels, xpixels = self.magpat.shape
        xraysf = rays * xpixels * rect.width / region.width
        yraysf = rays * ypixels * rect.height / region.height
        levels = max(1, int(log(min(xraysf, yraysf)/75)/log(self.rs.refine)))
        xraysf /= self.rs.refine**levels
        yraysf /= self.rs.refine**levels
        xrays = int(ceil(xraysf))
        yrays = int(ceil(yraysf))
        rect.width *= xrays/xraysf
        rect.height *= yrays/yraysf
        return rect, xrays, yrays, levels + 2

    def _run_threaded(self, rect, xrays, yrays, levels):
        num_threads = self.num_threads
        patches = libll.Patches(rect, levels - 1, xrays, yrays)
        y_indices = [j*yrays//num_threads for j in range(num_threads + 1)]
        y_values =  [rect.y + j*(rect.height/yrays) for j in y_indices]
        subpatches = []
        for j in range(num_threads):
            subrect = libll.Rect(rect.x, y_values[j], rect.width,
                                 y_values[j+1] - y_values[j])
            subhit = patches.hit_array[y_indices[j]:y_indices[j+1]]
            subpatches.append(libll.Patches(subrect, levels - 1, hit=subhit))
        threads = [threading.Thread(target=self.rs.get_subpatches,
                                    args=(subpatches[j],))
                   for j in range(1, num_threads)]
        for t in threads:
            t.start()
        self.rs.get_subpatches(subpatches[0])
        magpats = [self.magpat] + [numpy.zeros_like(self.magpat)
                                   for j in range(1, num_threads)]
        for t in threads:
            t.join()
        patches.num_patches = sum(p.num_patches for p in subpatches)
        subdomains = self.rs.refine
        x_indices = [i*xrays//subdomains for i in range(subdomains + 1)]
        x_values =  [rect.x + i*(rect.width/xrays) for i in x_indices]
        y_indices = [j*yrays//subdomains for j in range(subdomains + 1)]
        y_values =  [rect.y + j*(rect.height/yrays) for j in y_indices]
        queue = Queue.Queue()
        for j in range(subdomains):
            for i in range(subdomains):
                subrect = libll.Rect(x_values[i], y_values[j],
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
        self.rs.finalise_subpatches(magpats, patches)

    def _run_queue(self, queue, magpat, patches, index):
        hit = patches.hit_array
        try:
            while True:
                rect, i0, i1, j0, j1 = queue.get(False)
                subhit = numpy.ascontiguousarray(hit[j0:j1, i0:i1])
                subpatches = libll.Patches(rect, patches.level, hit=subhit)
                subpatches.num_patches = patches.num_patches
                self.rs.run_subpatches(magpat, subpatches, self.progress[index])
        except Queue.Empty:
            pass

def rayshoot(*args, **kwargs):
    """Compute a magnification pattern by ray shooting.

    The parameters are documented in the Rayshooter class.
    """
    rs = Rayshooter(*args, **kwargs)
    return rs.run()

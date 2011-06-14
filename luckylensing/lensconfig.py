# Lucky Lensing Library (http://github.com/smarnach/luckylensing)
# Copyright 2010 Sven Marnach

from __future__ import division, absolute_import
from math import sin, cos, log, sqrt, ceil
import numpy
from . import libll

class LensConfig(numpy.recarray):
    """A array of lens records describing a lens configuration.

    This is a NumPy recarray with fields and types of the records
    inherited from the libll.Lens structure.  You can access the
    columns an instance lenses as

        lenses.x         x-values of the lenses
        lenses.y         y-values of the lenses
        lenses.mass      masses of the lenses

    You can access a single lens as lenses[index] and its fields as
    lenses[index].x etc.

    Constructor:

        LensConfig(lenses=None, num_lenses=None)

        lenses           the lenses to store in this object; must be a
                         list of sequences of length 3 representing
                         x, y and mass of the respective lenses or a
                         NumPy array of records with 3 fields
        num_lenses       the number of lenses in the configuration; if
                         lenses is given, you don't need this parameter
        buf              passed on to ndarray.__new__()

    Examples:

        >>> lenses = LensConfig([(-0.5, 0, 0.5), (0.5, 0, 0.5)])
        >>> lenses.x
        array([-0.5,  0.5])
        >>> lenses.mass.sum()
        1.0
    """

    arg_name = "lenses"

    def __new__(cls, lenses=None, num_lenses=None, buf=None):
        dtype = numpy.dtype([(n, t._type_) for n, t in libll.Lens._fields_])
        if num_lenses is None:
            num_lenses = len(lenses)
        obj = numpy.recarray.__new__(cls, num_lenses, dtype=dtype, buf=buf)
        if lenses is not None:
            obj[:] = lenses
        return obj

    @classmethod
    def fromarray(cls, lenses):
        """Create class instance from the given NumPy array.

        The array must either be a two-dimensional array with three
        columns or a one-dimensional array of records with at least
        three fields.  In the latter case, there must be columns with
        the names 'x', 'y' and 'mass'.

        If the memory layout of the array is already as needed, the
        new instance will share the same memory.
        """
        dtype = numpy.dtype([(n, t._type_) for n, t in libll.Lens._fields_])
        if lenses.ndim == 2:
            if lenses.shape[1] != 3:
                raise ValueError("If a two-dimensional array is given, "
                                 "it must be of shape (num_lenses, 3)")
            lenses = lenses.view(dict(
                names=dtype.names, formats=[lenses.dtype]*3)).ravel()
        else:
            if lenses.ndim != 1:
                raise ValueError("Lens array must be 1d or 2d")
            if lenses.dtype.names != dtype.names:
                obj = cls(num_lenses=len(lenses))
                obj.x = lenses["x"]
                obj.y = lenses["y"]
                obj.mass = lenses["mass"]
                return obj
        if lenses.dtype == dtype:
            return cls(num_lenses=len(lenses), buf=lenses)
        return cls(lenses)

def binary_lenses(lens_distance, mass_ratio, total_mass=1.0):
    """Return a binary lens configuration.

    The returned LensConfig instance contains two lenses with
    barycentre in the origin.

    Parameters:

        lens_distance    distance between the two lenses
        mass_ratio       mass ratio of the two lenses
        total_mass       total mass of the two lenses
    """
    m0 = total_mass / (mass_ratio + 1.0)
    x1 = lens_distance / (mass_ratio + 1.0)
    return LensConfig(
        [(x1 - lens_distance, 0.0, m0), (x1, 0.0, total_mass - m0)])

def globular_cluster(num_stars=1000, total_mass=1.0, log_mass_stddev=0.0,
                     angle=0.0, random_seed=42):
    """Randomly generate a Gaussian globular cluster lens configuration.

    Returns a LensConfig instance describing a globular cluster.  The
    stars are distributed using a three-dimensional Gaussian
    distribution with an isotropic standard deviation of 1.0 and
    orthogonally projected to the xy-plane.  The centre of mass will
    corrected to be exactly at the coordinate origin up to double
    precision.

    Parameters:

        num_stars        number of stars in the cluster
        total_mass       sum of all star masses (will be met up to
                         double precision even for random masses)
        log_mass_stddev  standard deviation of log_10(mass);  defaults
                         to 0.0 for a completely uniform cluster
        angle            angle by which the cluster is rotated about
                         the y-axis before projecting to the xy-plane
        random_seed      seed used for NumPy's Mersenne Twister
    """
    lenses = LensConfig(num_lenses=num_stars)
    numpy.random.seed(random_seed)
    coords = numpy.random.multivariate_normal(
        [0., 0., 0.], numpy.identity(3), num_stars)
    star_mass = total_mass / num_stars
    if log_mass_stddev <= 0.0:
        lenses.mass.fill(star_mass)
    else:
        lenses.mass = numpy.random.lognormal(
            log(star_mass), log_mass_stddev * log(10.0), num_stars)
        lenses.mass *= star_mass / lenses.mass.mean()
    coords -= numpy.dot(lenses.mass, coords) / total_mass
    lenses.x = cos(angle) * coords[:,0] + sin(angle) * coords[:,1]
    lenses.y = coords[:,2]
    return lenses

def polygonal_lenses(num_stars=5, total_mass=1.0, angle=0.0):
    """Arrange lenses in the vertices of a regular polyhedron.

    Returns a LensConfig instance with lenses of equal mass
    distributed uniformly on a circle of radius 1.0 centred at the
    coordinate origin.  Useful to creative nice-looking images.

    Parameters:

        num_stars        number of stars
        total_mass       sum of all star masses
        angle            angle by which to rotate the polygon around
                         the origin
    """
    lenses = LensConfig(num_lenses=num_stars)
    phis = numpy.linspace(angle, angle + 2.*numpy.pi, num_stars + 1)[:-1]
    numpy.cos(phis, lenses.x)
    numpy.sin(phis, lenses.y)
    lenses.mass.fill(total_mass / num_stars)
    return lenses

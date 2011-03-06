from __future__ import division
from math import sin, cos, log, sqrt, ceil
import numpy
import libll

class LensConfig(numpy.recarray):
    """A array of lens records describing a lens configuration.

    This is a NumPy recarray with fields and types of the records
    inherited from the libll.Lens structure.  You can access the
    columns an instance lenses as

        lenses.x       x-values of the lenses
        lenses.y       y-values of the lenses
        lenses.mass    masses of the lenses

    You can access a single lens as lenses[index] and its fields as
    lenses[index].x etc.
    """

    arg_name = "lenses"

    def __new__(cls, num_lenses=None, buf=None, offset=0):
        dtype = [(n, t._type_) for n, t in libll.Lens._fields_]
        if num_lenses is None:
            if not isinstance(buf, numpy.ndarray):
                raise TypeError("If num_lenses is not given, buf must be "
                                "an numpy.ndarray instance")
            num_lenses = len(buf)
        return numpy.recarray.__new__(
            cls, num_lenses, dtype=dtype, buf=buf, offset=offset)

def binary_lenses(lens_distance, mass_ratio, total_mass=1.0):
    """Return a binary lens configuration.

    The returned LensConfig instance contains two lenses with
    barycentre in the origin.

    Parameters:

        lens_distance    distance between the two lenses
        mass_ratio       mass ratio of the two lenses
        total_mass       total mass of the two lenses
    """
    lenses = LensConfig(2)
    m0 = total_mass / (mass_ratio + 1.0)
    x1 = lens_distance / (mass_ratio + 1.0)
    lenses[:] = [(x1 - lens_distance, 0.0, m0), (x1, 0.0, total_mass - m0)]
    return lenses

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
        log_mass_stddev  standard deviation of log(mass);  defaults
                         to 0.0 for a completely uniform cluster
        angle            angle by which the cluster is rotated about
                         the y-axis before projecting to the xy-plane
        random_seed      seed used for NumPy's Mersenne Twister
    """
    lenses = LensConfig(num_stars)
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
    lenses = LensConfig(num_stars)
    phis = numpy.linspace(angle, angle + 2.*numpy.pi, num_stars + 1)[:-1]
    lenses.x = numpy.cos(phis)
    lenses.y = numpy.sin(phis)
    lenses.mass.fill(total_mass / num_stars)
    return lenses

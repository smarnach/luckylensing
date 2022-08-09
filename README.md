Lucky Lensing Library
=====================

The Lucky Lensing Library is a library and a graphical user interface
for computations in the context of [gravitational microlensing][1], an
astronomical phenomenon due to the "bending" of light by massive
objects.

The web home of the library is
<http://github.com/smarnach/luckylensing>.

Features:

  * High performance computations of magnification patterns by reverse
    ray shooting for arbitrary planar lens distributions using the
    thin-lens approximation.  It is particularly optimised for small
    (< 10,000) number of lenses.  Multi-threading is supported.

  * Convolution of magnification patterns with source profiles.
    Implementations for flat and Gaussian sources are provided.

  * Extraction of light curves for linear uniform source paths.

  * FITS input and output.

These features are accessible through an easy-to-use Python interface
or through a somewhat idiosyncratic GTK+ user interface.  The
ray-shooting code is written in C99.

The code is a work in progress and interfaces have not yet stabilised.
There is little documentation yet, mainly in the docstrings of the
Python interface.  The library might still be useful for
experimentation with magnification patterns though.

  -- Sven Marnach (sven (a) marnach.net)

Licence
-------

All files in the distribution are licenced under the "GNU Lesser
General Public License", version 3 or -- at your option -- any later
version.  See the file `COPYING` for details.

Bugs and patches
----------------

If you find any issues, notify me on the [issue tracker][3].  Or even
better, write a patch and send me a [pull request][4].

Prerequisites
-------------

The Lucky Lensing Library should work on Unix-like platforms, though
it is only tested on Linux so far.

To use the Python library, you need

  * gcc (tested with versions 4.3 and 4.4)

  * GNU make

  * Python 2.5 or higher, includig 3.x (without the GUI)

  * [NumPy][5] (probably any version will do)

For FITS I/O, you need in addition

  * [Astropy][6], version 5.0 or higher

For the GUI, you need in addition

  * [PyGtk][7]

  * [PyGtkImageView][8], version 1.2 or higher

  * The GUI does not work on Python 3.x

The examples additionally make use of

  * [Pillow][9], probably any recent version

Most of these dependencies are included in many Linux distributions,
PyGtkImageView being an exception.  I might get rid of the latter if I
feel like it one day.

Installation
------------

If you have git installed, you can clone the repository by calling

    git clone git://github.com/smarnach/luckylensing.git

Alternatively, you can [download a tarball][10] of the current
development version.

Then, to compile the C library, run "make" in the distribution
directory.  If your processor supports the SSE3 instruction set, you
can consider uncommenting the corresponding line in the file
`luckylensing/libll/Makefile` -- this will speed up the ray shooting a
bit.

Getting started
---------------

Have a look at examples/planet.py for a basic ray shooting example.
You can run this example by typing

    cd examples/
    ./planet.py

(i.e. you need to be in the examples directory to run it.)  The
example will create a sequence of images in the examples/magpats
directory visualizing the different caustic topologies for different
distances between planet and star.

Also check the GUI by

    cd gll/
    ./gll.py cluster.gll

Unfortunately, there's no documentation for the GUI so far.  Don't
hesitate to ask questions: (sven (a) marnach.net)

  [1]: https://en.wikipedia.org/wiki/Microlensing
  [3]: https://github.com/smarnach/luckylensing/issues
  [4]: https://help.github.com/pull-requests/
  [5]: https://numpy.scipy.org/
  [6]: https://www.astropy.org/
  [7]: https://www.pygtk.org/
  [8]: https://trac.bjourne.webfactional.com/
  [9]: https://python-pillow.org/
 [10]: https://github.com/smarnach/luckylensing/tarball/master

Copyright 2010 Sven Marnach

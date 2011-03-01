from __future__ import division
import libll
import logging
import sys

logger = logging.getLogger("luckylensing")
logger.setLevel(logging.DEBUG)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

def rectangle(x0=None, y0=None, x1=None, y1=None,
              width=None, height=None, radius=None):
    """Return a new libll.Rect instance.

    Parameters:
        Provide either

            Two out of x0, x1, width and
            two out of y0, y1, height

        or

            radius and optionally x0 and y0

        In the first case, the missing parameters will be substituted
        such that they fulfil

            width = x1 - x0
            height = y1 - y0

        The second case is a short-cut for

            region(x0 - radius, y0 - radius, x0 + radius, y0 + radius)

        where x0 and y0 default to 0.0.

    Examples:
        The following calls are equivalent:

            region(-1, -1, 1, 1)
            region(x0=-1, y0=-1, x1=1, y1=1)
            region(-1, -1, width=2, height=2)
            region(0, 0, radius=1)
    """
    if radius is not None:
        if (x1, y1, width, height) != (None,) * 4:
            raise TypeError("If 'radius' is given, 'x1', 'y1', "
                            "'width' and 'height' are not allowed.")
        if x0 is None:
            x0 = 0.0
        if y0 is None:
            y0 = 0.0
        return libll.Rect(x0 - radius, y0 - radius, 2 * radius, 2 * radius)
    if x0 is None:
        x0 = x1 - width
    elif width is None:
        width = x1 - x0
    else:
        if x1 is not None:
            raise TypeError("Only two out of 'x0', 'x1' and 'width' "
                            "may be provided.")
    if y0 is None:
        y0 = y1 - height
    elif height is None:
        height = y1 - y0
    else:
        if y1 is not None:
            raise TypeError("Only two out of 'y0', 'y1' and 'height' "
                            "may be provided.")
    return libll.Rect(x0, y0, width, height)

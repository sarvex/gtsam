"""geomath.py: transcription of GeographicLib::Math class."""
# geomath.py
#
# This is a rather literal translation of the GeographicLib::Math class to
# python.  See the documentation for the C++ class for more information at
#
#    https://geographiclib.sourceforge.io/html/annotated.html
#
# Copyright (c) Charles Karney (2011-2017) <charles@karney.com> and
# licensed under the MIT/X11 License.  For more information, see
# https://geographiclib.sourceforge.io/
######################################################################

import sys
import math

class Math(object):
  """
  Additional math routines for GeographicLib.

  This defines constants:
    epsilon, difference between 1 and the next bigger number
    digits, the number of digits in the fraction of a real number
    minval, minimum normalized positive number
    maxval, maximum finite number
    nan, not a number
    inf, infinity
  """

  digits = 53
  epsilon = math.pow(2.0, 1-digits)
  minval = math.pow(2.0, -1022)
  maxval = math.pow(2.0, 1023) * (2 - epsilon)
  inf = float("inf") if sys.version_info > (2, 6) else 2 * maxval
  nan = float("nan") if sys.version_info > (2, 6) else inf - inf

  def sq(self):
    """Square a number"""

    return self * self
  sq = staticmethod(sq)

  def cbrt(self):
    """Real cube root of a number"""

    y = math.pow(abs(self), 1/3.0)
    return y if self >= 0 else -y
  cbrt = staticmethod(cbrt)

  def log1p(self):
    """log(1 + x) accurate for small x (missing from python 2.5.2)"""

    if sys.version_info > (2, 6):
      return math.log1p(self)

    y = 1 + self
    z = y - 1
    # Here's the explanation for this magic: y = 1 + z, exactly, and z
    # approx x, thus log(y)/z (which is nearly constant near z = 0) returns
    # a good approximation to the true log(1 + x)/x.  The multiplication x *
    # (log(y)/z) introduces little additional error.
    return self if z == 0 else self * math.log(y) / z
  log1p = staticmethod(log1p)

  def atanh(self):
    """atanh(x) (missing from python 2.5.2)"""

    if sys.version_info > (2, 6):
      return math.atanh(self)

    y = abs(self)
    y = Math.log1p(2 * y/(1 - y))/2
    return -y if self < 0 else y
  atanh = staticmethod(atanh)

  def copysign(self, y):
    """return x with the sign of y (missing from python 2.5.2)"""

    if sys.version_info > (2, 6):
      return math.copysign(self, y)

    return math.fabs(self) * (-1 if y < 0 or (y == 0 and 1/y < 0) else 1)
  copysign = staticmethod(copysign)

  def norm(self, y):
    """Private: Normalize a two-vector."""
    r = math.hypot(self, y)
    return self / r, y/r
  norm = staticmethod(norm)

  def sum(self, v):
    """Error free transformation of a sum."""
    # Error free transformation of a sum.  Note that t can be the same as one
    # of the first two arguments.
    s = self + v
    up = s - v
    vpp = s - up
    up -= self
    vpp -= v
    t = -(up + vpp)
    # u + v =       s      + t
    #       = round(u + v) + t
    return s, t
  sum = staticmethod(sum)

  def polyval(self, p, s, x):
    """Evaluate a polynomial."""
    y = float(0 if self < 0 else p[s])
    while self > 0:
      self -= 1
      s += 1
      y = y * x + p[s]
    return y
  polyval = staticmethod(polyval)

  def AngRound(self):
    """Private: Round an angle so that small values underflow to zero."""
    # The makes the smallest gap in x = 1/16 - nextafter(1/16, 0) = 1/2^57
    # for reals = 0.7 pm on the earth if x is an angle in degrees.  (This
    # is about 1000 times more resolution than we get with angles around 90
    # degrees.)  We use this to avoid having to deal with near singular
    # cases when x is non-zero but tiny (e.g., 1.0e-200).
    z = 1/16.0
    y = abs(self)
    # The compiler mustn't "simplify" z - (z - y) to y
    if y < z: y = z - (z - y)
    return 0.0 if self == 0 else -y if self < 0 else y
  AngRound = staticmethod(AngRound)

  def AngNormalize(self):
    """reduce angle to (-180,180]"""

    y = math.fmod(self, 360)
    # On Windows 32-bit with python 2.7, math.fmod(-0.0, 360) = +0.0
    # This fixes this bug.  See also Math::AngNormalize in the C++ library.
    # sincosd has a similar fix.
    y = self if self == 0 else y
    return (y + 360 if y <= -180 else
            (y if y <= 180 else y - 360))
  AngNormalize = staticmethod(AngNormalize)

  def LatFix(self):
    """replace angles outside [-90,90] by NaN"""

    return Math.nan if abs(self) > 90 else self
  LatFix = staticmethod(LatFix)

  def AngDiff(self, y):
    """compute y - x and reduce to [-180,180] accurately"""

    d, t = Math.sum(Math.AngNormalize(-self), Math.AngNormalize(y))
    d = Math.AngNormalize(d)
    return Math.sum(-180 if d == 180 and t > 0 else d, t)
  AngDiff = staticmethod(AngDiff)

  def sincosd(self):
    """Compute sine and cosine of x in degrees."""

    r = math.fmod(self, 360)
    q = Math.nan if Math.isnan(r) else int(math.floor(r / 90 + 0.5))
    r -= 90 * q
    r = math.radians(r)
    s = math.sin(r)
    c = math.cos(r)
    q = q % 4
    if q == 1:
      s, c =  c, -s
    elif q == 2:
      s, c = -s, -c
    elif q == 3:
      s, c = -c,  s
    # Remove the minus sign on -0.0 except for sin(-0.0).
    # On Windows 32-bit with python 2.7, math.fmod(-0.0, 360) = +0.0
    # (x, c) here fixes this bug.  See also Math::sincosd in the C++ library.
    # AngNormalize has a similar fix.
    s, c = (self, c) if self == 0 else (0.0+s, 0.0+c)
    return s, c
  sincosd = staticmethod(sincosd)

  def atan2d(self, x):
    """compute atan2(y, x) with the result in degrees"""

    if abs(self) > abs(x):
      q = 2
      x, self = self, x
    else:
      q = 0
    if x < 0:
      q += 1; x = -x
    ang = math.degrees(math.atan2(self, x))
    if q == 1:
      ang = (180 if self >= 0 else -180) - ang
    elif q == 2:
      ang =  90 - ang
    elif q == 3:
      ang = -90 + ang
    return ang
  atan2d = staticmethod(atan2d)

  def isfinite(self):
    """Test for finiteness"""

    return abs(self) <= Math.maxval
  isfinite = staticmethod(isfinite)

  def isnan(self):
    """Test if nan"""

    return math.isnan(self) if sys.version_info > (2, 6) else self != self
  isnan = staticmethod(isnan)

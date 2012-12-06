"""Simple operations on generic objects."""

from __future__ import generators
import copy
import string


class Enum(object):
  """An Enum has attributes set to the given values.

  Spaces and dashes in attrs are converted to underscores, values are left
  alone.

  The attributes and values can be expressed as either:
      Enum(str, str)  in which case attr == value
      e = Enum('a', 'b')
      e.a == 'a'
      e.b == 'b'
  or:
      Enum((str, str), (str, str)) in which case attributes and values are
      taken from the tuples as (attr, value).
      e = Enum(('a', 'eh'), ('b', '2 b'))
      e.a == 'eh'
      e.b == '2 b'
  Mixing the two methods is also allowed:
    e = Enum('a', ('b', 'to bee or buzz'))
      e.a == 'a'
      e.b == 'to bee or buzz'

  This is intended to be an ad-hoc enumeration type.  If you say
    color = Enum('red', 'green', 'blue')
  you can then write color.red instead of 'red', and a typo will become an
  AttributeError instead of silently generating bad HTML, a bad SQL query, or
  whatever.

  The Enum* accessor methods are guaranteed to return the attributes and values
  in the order used when the Enum was created.
  """

  def __init__(self, *vals):
    instance_attrs = []
    for attr in vals:
      if isinstance(attr, tuple):
        attr, val = attr
      else:
        val = attr
      safe_attr = attr.translate(string.maketrans(' -', '__'))
      if getattr(self, safe_attr, None):
        raise KeyError('enum attr "%s" conflicts with "%s"' % (
            attr, getattr(self, safe_attr)))
      instance_attrs.append(safe_attr)
      setattr(self, safe_attr, val)
    self.__all__ = instance_attrs

  def EnumAttrs(self):
    """Return list of Enum attributes. Like dict.iterkeys."""
    return self.__all__

  def EnumValues(self):
    """Return list of Enum values. Like dict.itervalues."""
    return [getattr(self, attr) for attr in self.__all__]

  def EnumItems(self):
    """Return list of Enum (attribute, value) tuples. Like dict.iteritems."""
    return [(attr, getattr(self, attr)) for attr in self.__all__]


from ctypes import *
from typing import Tuple

c_int.__invert__ = lambda x: not x
c_int8.__invert__ = lambda x: not x
c_uint8.__invert__ = lambda x: not x
c_int16.__invert__ = lambda x: not x
c_uint16.__invert__ = lambda x: not x
c_int32.__invert__ = lambda x: not x
c_uint32.__invert__ = lambda x: not x
c_int64.__invert__ = lambda x: not x
c_uint64.__invert__ = lambda x: not x

size_t = c_uint64

# PRIu64 is a format specifier, introduced in C99, for printing uint64_t
PRIu64 = "llu"
PRIx64 = "I64x"
PRIX64 = "I64X"
PRIs64 = "lld"


def enumeration(cls=None):
    """Annotate the class as an enumeration because we could not use Enum"""
    return cls

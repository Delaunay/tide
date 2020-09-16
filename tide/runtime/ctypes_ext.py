from ctypes import *

c_int.__invert__ = lambda x: not x
c_int8.__invert__ = lambda x: not x
c_uint8.__invert__ = lambda x: not x
c_int16.__invert__ = lambda x: not x
c_uint16.__invert__ = lambda x: not x
c_int32.__invert__ = lambda x: not x
c_uint32.__invert__ = lambda x: not x
c_int64.__invert__ = lambda x: not x
c_uint64.__invert__ = lambda x: not x

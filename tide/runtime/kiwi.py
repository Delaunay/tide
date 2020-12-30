# Decorator defined to make kiwi file compile using Python interpreter
# used to hold the missing metadata to generate C++

def struct(*args, **kwargs):
    pass


def const(*args, **kwargs):
    pass


def abstract(*args, **kwargs):
    pass


def virtual(*args, **kwargs):
    pass


def novirtual(*arg, **kwargs):
    pass


import typing


class ForwardRef(typing._Final, _root=True):
    """Internal wrapper to hold a forward reference."""

    __slots__ = ('__forward_arg__', '__forward_code__',
                 '__forward_evaluated__', '__forward_value__',
                 '__forward_is_argument__')

    def __init__(self, arg, is_argument=True):
        if not isinstance(arg, str):
            raise TypeError(f"Forward reference must be a string -- got {arg!r}")

        code = None
        try:
            code = compile(arg, '<string>', 'eval')
        except SyntaxError:
            # This is because kiwi use raw C++ types in forward ref
            pass
            # raise SyntaxError(f"Forward reference must be an expression -- got {arg!r}")
        self.__forward_arg__ = arg
        self.__forward_code__ = code
        self.__forward_evaluated__ = False
        self.__forward_value__ = None
        self.__forward_is_argument__ = is_argument

    def _evaluate(self, globalns, localns):
        if not self.__forward_evaluated__ or localns is not globalns:
            if globalns is None and localns is None:
                globalns = localns = {}
            elif globalns is None:
                globalns = localns
            elif localns is None:
                localns = globalns
            self.__forward_value__ = typing._type_check(
                eval(self.__forward_code__, globalns, localns),
                "Forward references must evaluate to types.",
                is_argument=self.__forward_is_argument__)
            self.__forward_evaluated__ = True
        return self.__forward_value__

    def __eq__(self, other):
        if not isinstance(other, ForwardRef):
            return NotImplemented
        return (self.__forward_arg__ == other.__forward_arg__ and
                self.__forward_value__ == other.__forward_value__)

    def __hash__(self):
        return hash((self.__forward_arg__, self.__forward_value__))

    def __repr__(self):
        return f'ForwardRef({self.__forward_arg__!r})'

typing.ForwardRef = ForwardRef

from typing import *

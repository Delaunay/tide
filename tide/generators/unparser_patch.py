# coding: utf-8
from __future__ import absolute_import
from six.moves import cStringIO
from astunparse.unparser import Unparser


def patch(Unparser):
    original_Constant = Unparser._Constant

    def new_Constant(self, t):
        if hasattr(t, 'docstring') and t.docstring:
            self.write('"""')
            self.write(str(t.value))
            self.write('"""')
        else:
            original_Constant(self, t)

    Unparser._Constant = new_Constant
    return Unparser


def unparse(tree):
    v = cStringIO()
    patch(Unparser)(tree, file=v)
    return v.getvalue()

# -*- coding: utf-8 -*-
__author__ = 'Pierre Delaunay'
from tide.runtime.kiwi import *
from .expression import ScalarReal, Unknown, Addition, Subtraction, Multiplication, Exp, Log, Divide, Pow


class Visitor:
    def __init__(self):
        pass

    @abstract
    def scalar(self, s: 'ScalarReal*'):
        raise NotImplemented

    @abstract
    def unknown(self, u: 'Unknown*'):
        raise NotImplemented

    @abstract
    def add(self, a: 'Addition*'):
        raise NotImplemented

    @abstract
    def sub(self, s: 'Subtraction*'):
        raise NotImplemented

    @abstract
    def mult(self, m: 'Multiplication*'):
        raise NotImplemented

    @abstract
    def exp(self, e: 'Exp*'):
        raise NotImplemented

    @abstract
    def log(self, l: 'Log*'):
        raise NotImplemented

    @abstract
    def div(self, d: 'Divide*'):
        raise NotImplemented

    @abstract
    def pow(self, p: 'Pow*'):
        raise NotImplemented

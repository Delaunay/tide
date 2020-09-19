import signal
import time

import logging
log = logging.getLogger('TIDE')

import clang.cindex
from clang.cindex import Cursor, CursorKind, Type, SourceLocation, TypeKind, TranslationUnit


class SignalReceived(Exception):
    pass


class Protected(object):
    def __init__(self, kind, name):
        self.signal_received = None
        self.handlers = dict()
        self.start = 0
        self.kind = kind
        self.name = name

    def __enter__(self):
        self.signal_received = False
        self.start = time.time()
        # self.handlers[signal.SIGINT] = signal.signal(signal.SIGINT, self.handler)
        # self.handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, self.handler)
        self.handlers[signal.SIGSEGV] = signal.signal(signal.SIGSEGV, self.handler)
        return self

    def handler(self, sig, frame):
        print(f'Delaying signal to finish operations')
        self.signal_received = (sig, frame)

        with open('error.log', 'w') as f:
            f.write(f'{self.kind} {self.name}\n')

        self.handlers[self.signal_received[0]](*self.signal_received)

    def __exit__(self, type, value, traceback):
        # signal.signal(signal.SIGINT, self.handlers[signal.SIGINT])
        # signal.signal(signal.SIGTERM, self.handlers[signal.SIGTERM])
        signal.signal(signal.SIGSEGV, self.handlers[signal.SIGSEGV])

        if self.signal_received:
            log.warning(f'Termination was delayed by {time.time() - self.start:.4f} s')
            # self.handlers[self.signal_received[0]](*self.signal_received)


bad_attributes = {
    # TLS: thread local storage
    CursorKind.MACRO_DEFINITION: {'tls_kind', 'storage_class'},
    CursorKind.MACRO_INSTANTIATION: {'tls_kind', 'storage_class'},
    CursorKind.DECL_STMT: {'tls_kind'},
    CursorKind.PAREN_EXPR: {'tls_kind'},
    CursorKind.CSTYLE_CAST_EXPR: {'tls_kind'},
    CursorKind.INTEGER_LITERAL: {'tls_kind'},
    CursorKind.STRING_LITERAL: {'tls_kind'},
    CursorKind.UNARY_OPERATOR: {'tls_kind'},
    CursorKind.BINARY_OPERATOR: {'tls_kind'},
    CursorKind.DECL_REF_EXPR: {'tls_kind'},
    CursorKind.FLOATING_LITERAL: {'tls_kind'},
    CursorKind.CALL_EXPR: {'tls_kind'},
}


def join_args(*args):
    return ' '.join(str(a) for a in args)


def show_elem(elem: Cursor, print_fun=print):
    new_print = lambda *args: print_fun(join_args(*args))

    new_print(elem.kind)
    avoid_attributes = bad_attributes.get(elem.kind, set())

    for attr_name in sorted(dir(elem)):
        if attr_name.startswith('__'):
            continue

        if attr_name in avoid_attributes:
            continue

        attr = None
        try:
            attr = getattr(elem, attr_name)
            pass
        except:
            continue

        if callable(attr):
            v = None
            try:
                pass
                v = attr()
            except:
                pass

            k = None
            if hasattr(v, 'kind'):
                k = v.kind

            new_print('   ', attr_name, v, k)
        else:
            new_print('   ', attr_name, attr)


def traverse(elem: Cursor, depth: int = 0, print_fun=print):
    indent = ' ' * depth

    if elem is None:
        print_fun(f'{indent}None')
        return
    print_fun(f'{indent}{elem.kind}')

    if hasattr(elem, 'get_children'):
        for child in elem.get_children():
            traverse(child, depth + 1, print_fun=print_fun)


def show_file(filename):
    index = clang.cindex.Index.create()
    tu = index.parse(filename, options=0x01)

    for diag in tu.diagnostics:
        print(diag.format())

    for elem in tu.cursor.get_children():
        show_elem(elem)

        if elem.spelling == '__GNUC__':
            break

        pass


if __name__ == '__main__':
    show_file('/usr/include/SDL2/SDL.h')

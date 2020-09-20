import logging

import ast
import tide.generators.nodes as T
from tide.generators.debug import d
from tide.utils.trie import Trie

log = logging.getLogger('API')


acronyms_db = Trie()
acronyms_db.insert('GL')
acronyms_db.insert('RLE')   # Run Length Encoding


def parse_sdl_name(name):
    """Parse SDL naming convention and explode it by components

    Examples
    --------
    >>> parse_sdl_name('SDL_GetIndex')
    ('SDL', ['get', 'index'])

    >>> parse_sdl_name('SDL_GetIndexRLE')
    ('SDL', ['get', 'index', 'RLE'])
    """
    # <module>_CamelCase
    try:
        module, name = name.split('_', maxsplit=1)
    except ValueError:
        return ' ', [name]

    # global acronyms_db
    # acronyms = acronyms_db

    all_upper = False
    names = []
    buffer = ''
    c: str

    for i, c in enumerate(name):
        if c == '_':
            continue

        if c.isupper():
            if buffer and not all_upper:
                names.append(buffer.lower())
                buffer = ''
                all_upper = True

            buffer += c
        else:
            buffer += c
            all_upper = False
    else:
        if buffer:
            if not all_upper:
                buffer = buffer.lower()

            names.append(buffer)

    return module, names


class APIPass:
    """Generate a more friendly API for C bindings"""
    def __init__(self):
        self.dispatcher = {
            'Expr': self.expression,
            'Assign': self.assign,
            'ClassDef': self.class_definition,
            'FunctionDef': self.function_definition
        }
        self.types = dict()

    def class_definition(self, class_def: T.ClassDef, depth):
        self.types[class_def.name] = class_def
        return class_def

    def function_definition(self, function_def: T.FunctionDef, depth):
        return function_def

    def assign(self, expr: T.Assign, depth):
        return expr

    def expression(self, expr: T.Expr, depth):
        return T.Expr(self.dispatch(expr.value, depth))

    def generate(self, module: T.Module, depth=0):
        new_module: T.Module = ast.Module()
        new_module.body = []

        for expr in module.body:
            expr = self.dispatch(expr, depth + 1)

            if expr is not None:
                new_module.body.append(expr)

        return new_module

    def dispatch(self, expr, depth):
        handler = self.dispatcher.get(expr.__class__.__name__, None)

        if handler is None:
            print(expr)
            assert False

        return handler(expr, depth)


def generate_api_bindings():
    from tide.generators.binding_generator import BindingGenerator, generate_bindings

    bindings = BindingGenerator.run('/usr/include/SDL2/SDL.h')

    api = APIPass()

    bindings = api.generate(bindings)

    generate_bindings(bindings)


if __name__ == '__main__':
    import sys
    sys.stderr = sys.stdout

    logging.basicConfig(stream=sys.stdout)
    log.setLevel(logging.DEBUG)

    logging.getLogger(__name__).setLevel(logging.DEBUG)
    logging.getLogger('tide.generators.binding_generator').setLevel(logging.INFO)
    logging.getLogger('tide.generators.operator_precedence').setLevel(logging.INFO)

    generate_api_bindings()


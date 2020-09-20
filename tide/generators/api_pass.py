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


def class_name(*names):
    return ''.join([n.capitalize() for n in names])


def function_name(*names):
    return '_'.join([n.lower() for n in names])


def match(value, type, *expr):
    if value.__class__.__name__ != type:
        return False

    p = value

    for attr, name in expr:
        if not hasattr(p, attr):
            return False

        p = getattr(p, attr)

        if p.__class__.__name__ != name:
            return False

    return True


class APIPass:
    """Generate a more friendly API for C bindings"""
    def __init__(self):
        self.dispatcher = {
            'Expr': self.expression,
            'Assign': self.assign,
            'ClassDef': self.class_definition,
            'FunctionDef': self.function_definition
        }
        self.ctypes = dict()
        self.wrappers = dict()
        self.names = Trie()

    def class_definition(self, class_def: T.ClassDef, depth):
        self.ctypes[class_def.name] = class_def

        self_wrap = self.wrappers.get(class_def.name)
        if self_wrap is None:
            _, names = parse_sdl_name(class_def.name)

            self_wrap = T.ClassDef(class_name(*names))
            self.wrappers[class_def.name] = self_wrap
            self_wrap.body.append(T.AnnAssign(T.Name('handle'), T.Name(class_def.name), None))

        return class_def

    def function_definition(self, function_def: T.FunctionDef, depth):
        return function_def

    SELF = T.Attribute(T.Name('self'), 'handle')
    ARGS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.lower()

    def process_bind_call(self, call: T.Call, parent):
        fun_name = call.args[0].s
        ctype_args: T.List = call.args[1]
        ctype_return = call.args[2]

        if match(ctype_args, 'Name'):
            return parent

        if not match(ctype_args, 'List'):
            return parent

        self_name = None
        self_arg: T.Call = ctype_args.elts[0]

        # Extract the self type
        # SDL_RenderSetLogicalSize = _bind('SDL_RenderSetLogicalSize', [POINTER(SDL_Renderer), c_int, c_int], c_int)
        #                                                                       ^~~~~~~~~~~^
        if match(self_arg, 'Call', ('func', 'Name')) and self_arg.func.id == 'POINTER' and match(self_arg.args[0], 'Name'):
            self_name = self_arg.args[0].id

        self_def = self.ctypes.get(self_name)
        if not self_def and match(self_def, 'ClassDef'):
            return parent

        # Generate our new python class that will wrap the ctypes
        self_wrap: T.ClassDef = self.wrappers.get(self_name)
        if self_wrap is None:
            return parent

        _, names = parse_sdl_name(fun_name)
        ctype_args = list(ctype_args.elts[1:])

        new_fun = T.FunctionDef(function_name(*names))
        new_fun.args = T.Arguments(args=[T.Arg('self')] + [T.Arg(n, t) for n, t in zip(self.ARGS, ctype_args)])
        new_fun.body.append(
            T.Return(T.Call(T.Name(fun_name), [self.SELF] + [T.Name(self.ARGS[i]) for i in range(len(ctype_args))]))
        )
        new_fun.returns = ctype_return
        self_wrap.body.append(new_fun)

        # We are ready to move our function from
        # print(object_type)
        return parent

    def assign(self, expr: T.Assign, depth):
        if match(expr.value, 'Call', ('func', 'Name')) and expr.value.func.id == '_bind':
            expr = self.process_bind_call(expr.value, expr)

        return expr

    def expression(self, expr: T.Expr, depth):
        values = self.dispatch(expr.value, depth)
        if isinstance(values, (tuple, list)):
            return [T.Expr(v) for v in values]

        return T.Expr(values)

    def generate(self, module: T.Module, depth=0):
        new_module: T.Module = ast.Module()
        new_module.body = []

        for expr in module.body:
            self.dispatch(expr, depth + 1)

        # insert our new bindings at the end
        for k, v in self.wrappers.items():
            module.body.append(v)
        return module

    def dispatch(self, expr, depth) -> T.Expr:
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


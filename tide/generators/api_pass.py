import ast
from collections import defaultdict
import copy
import logging
from typing import List

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

    >>> parse_sdl_name('SDL_GL_BindTexture')
    ('SDL', ['GL', 'bind', 'texture'])

    >>> parse_sdl_name('SDL_GLprofile')
    ('SDL', ['GL', 'profile'])
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
        # handles GL_Bind
        if c == '_':
            if not all_upper:
                buffer = buffer.lower()

            names.append(buffer)
            buffer = ''
            all_upper = False
            continue

        if c.isupper():
            if buffer and not all_upper:
                names.append(buffer.lower())
                buffer = ''

            buffer += c
            all_upper = True

        # handles: GLprofile
        elif len(buffer) > 1 and all_upper:
            names.append(buffer)
            buffer = c
        else:
            buffer += c
            all_upper = False
    else:
        if buffer:
            if not all_upper:
                buffer = buffer.lower()

            names.append(buffer)

    return module, names


def capitalize(s: str) -> str:
    if s.isupper():
        return s
    return s.capitalize()


def class_name(*names):
    return ''.join([capitalize(n) for n in names])


def lower(s: str) -> str:
    if s.isupper():
        return s
    return s.lower()


def function_name(*names):
    return '_'.join([lower(n) for n in names])


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
        self.wrappers_2_ctypes = dict()
        # keep the order to know if we can annotate with Name of with string
        self.wrapper_order = dict()
        # we will remove wrappers that do not have methods
        # i.e they are data struct only
        self.wrapper_method_count = defaultdict(int)
        self.names = Trie()
        self.rename_types = dict()
        self.current_class_name = None

    def class_definition(self, class_def: T.ClassDef, depth):
        self.ctypes[class_def.name] = class_def

        # Opaque struct: move on
        if class_def.name[0] == '_':
            return class_def

        self_wrap = self.wrappers.get(class_def.name)
        if self_wrap is None:
            if T.Name('enumeration') in class_def.decorator_list:
                return class_def

            _, names = parse_sdl_name(class_def.name)

            cl_name = class_name(*names)
            self_wrap = T.ClassDef(cl_name)
            self.wrappers[class_def.name] = self_wrap
            self.wrappers_2_ctypes[self_wrap.name] = class_def.name
            self.wrapper_order[self_wrap.name] = len(self.wrappers)

            self_wrap.body.append(T.AnnAssign(T.Name('handle'), T.Name(class_def.name), T.Name('None')))

            # Factory to build the wrapper form the ctype
            # create an uninitialized version of the object and set the handle
            from_ctype = T.FunctionDef('from_handle', decorator_list=[T.Name('staticmethod')])
            from_ctype.args = T.Arguments(args=[T.Arg('a', T.Name(class_def.name))])
            from_ctype.returns = T.Constant(cl_name)
            from_ctype.body = [
                T.Assign([T.Name('b')], T.Call(T.Attribute(T.Name('object'), '__new__'), [T.Name(cl_name)])),
                T.Assign([T.Attribute(T.Name('b'), 'handle')], T.Name('a')),
                T.Return(T.Name('b'))
            ]

            self_wrap.body.append(from_ctype)
            self.rename_types[T.Call(T.Name('POINTER'), [T.Name(class_def.name)])] = cl_name

        return class_def

    def function_definition(self, function_def: T.FunctionDef, depth):
        return function_def

    SELF_HANDLE = T.Attribute(T.Name('self'), 'handle')
    ARGS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.lower()

    def rename(self, n):
        new_name = self.rename_types.get(n, None)
        if new_name:
            arg_type_order = self.wrapper_order.get(new_name, None)
            class_order = self.wrapper_order.get(self.current_class_name, None)

            # arg type is defined after current class
            if arg_type_order and class_order and arg_type_order > class_order:
                return T.Constant(new_name)

            if new_name == self.current_class_name:
                return T.Constant(new_name)

            return T.Name(new_name)
        return n

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
        self.current_class_name = self_wrap.name

        new_fun = T.FunctionDef(function_name(*names))
        new_fun.returns = self.rename(ctype_return)

        # we need to convert the result to our new class
        ccall = T.Call(T.Name(fun_name), [self.SELF_HANDLE] + [T.Name(self.ARGS[i]) for i in range(len(ctype_args))])

        if new_fun.returns != ctype_return:
            cast_to = new_fun.returns

            if isinstance(new_fun.returns, T.Constant):
                cast_to = T.Name(new_fun.returns.value)

            ccall = T.Call(T.Attribute(cast_to, 'from_handle'), [ccall])

        new_fun.args = T.Arguments(args=[T.Arg('self')] + [T.Arg(n, self.rename(t)) for n, t in zip(self.ARGS, ctype_args)])
        new_fun.body = [
            # self.handle_is_not_none,
            T.Return(ccall)
        ]
        self_wrap.body.append(new_fun)

        # try to find destructor and constructor functions
        for i, n in enumerate(names):
            arg_n = len(new_fun.args.args)

            # check if the function is named destroy + class_name
            if arg_n == 1 and n == 'destroy' and i + 2 == len(names) and names[i + 1] == self_wrap.name.lower():
                destructor = copy.deepcopy(new_fun)
                destructor.name = '__del__'
                self_wrap.body.append(destructor)
                break

            # sdl is not consistent with that one
            if n == 'free':
                destructor = copy.deepcopy(new_fun)
                destructor.name = '__del__'
                self_wrap.body.append(destructor)


        self.wrapper_method_count[self.current_class_name] += 1
        self.current_class_name = None

        # We are ready to move our function from
        # print(object_type)
        return parent

    handle_is_not_none = T.Assert(
        test=T.Compare(
            left=T.Attribute(value=T.Name(id='self', ctx=T.Load()), attr='handle', ctx=T.Load()),
            ops=[T.IsNot()],
            comparators=[T.Constant(value=None, kind=None)]), msg=None)

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
            if isinstance(v, T.ClassDef):
                if self.wrapper_method_count.get(v.name, 0) > 0:
                    module.body.append(v)

                elif v.name in self.wrappers_2_ctypes:
                    c_struct = self.wrappers_2_ctypes.get(v.name)
                    # make it an alias for the ctype
                    module.body.append(T.Expr(T.Assign([T.Name(v.name)], T.Name(c_struct))))

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


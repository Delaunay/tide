import ast
from collections import defaultdict
import copy
import logging
import re
from typing import List

import tide.generators.nodes as T
from tide.generators.binding_generator import c_identifier
from tide.generators.debug import d
from tide.utils.trie import Trie

log = logging.getLogger('API')


acronyms_db = Trie()
acronyms_db.insert('GL')
acronyms_db.insert('RLE')   # Run Length Encoding
acronyms_db.insert('YUV')   # Luma, Blue, Red


def get_ast(code):
    mod: T.Module = ast.parse(code)
    return mod.body[0]


def split_on_case_change(name: str, separators=None):
    """

    Examples
    --------
    >>> split_on_case_change('SDL_GetIndex', {'_'})
    ['SDL', 'G', 'et', 'I', 'ndex']

    >>> split_on_case_change('SDL_GetIndexRLE', {'_'})
    ['SDL', 'G', 'et', 'I', 'ndex', 'RLE']

    >>> split_on_case_change('SDL_GL_BindTexture', {'_'})
    ['SDL', 'GL', 'B', 'ind', 'T', 'exture']

    >>> split_on_case_change('SDL_GLprofile', {'_'})
    ['SDL', 'GL', 'profile']

    >>> split_on_case_change('SDL_UpdateYUVTexture', {'_'})
    ['SDL', 'U', 'pdate', 'YUVT', 'exture']
    """
    is_lower = name[0].islower()
    buffer = ''
    result = []

    if separators is None:
        separators = set()

    i = 0
    while i < len(name):
        n = name[i]

        if n in separators:
            result.append(buffer)
            buffer = name[i + 1]
            is_lower = name[i + 1].islower()
            i += 2
            continue
        elif is_lower is n.islower():
            buffer += n
            i += 1
        else:
            result.append(buffer)
            buffer = name[i]
            is_lower = name[i].islower()
            i += 1

    if buffer:
        result.append(buffer)

    return result


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

    This case is problematic
    >>> parse_sdl_name('SDL_UpdateYUVTexture')
    ('SDL', ['update', 'YUV', 'texture'])
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

            # YUVT handling, stop when the acronym is full
            trie = acronyms_db.find(buffer)
            if all_upper and trie and trie.leaf:
                names.append(buffer)
                buffer = ''

            buffer += c
            all_upper = True

        # handles: GLprofile
        elif c.islower() and len(buffer) > 1 and all_upper:
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


def get_kwarg_arg(name, kwargs: List[T.Keyword], default):
    for kwarg in kwargs:
        if kwarg.arg == name:
            return kwarg.value

    return default


def capitalize(s: str) -> str:
    if s.isupper() and acronyms_db.find(s):
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


RESERVED_KEYWORDS = {
    'raise'
}


def clean_name(original_name, to_remove):
    if original_name.startswith('__'):
        return original_name

    name = (original_name.replace(to_remove, '')
                         .replace('__', '_'))

    s = 0
    if name[0] == '_':
        s = 1

    e = len(name)
    if name[-1] == '_':
        e = -1

    new_name = name[s:e]

    if not re.match(c_identifier, new_name):
        return original_name

    if new_name in RESERVED_KEYWORDS:
        return original_name

    return new_name


class APIPass:
    """Generate a more friendly API for C bindings

    Notes
    -----
    * removes the explicit library namespace from the name of functions and struct
    * Rewrites functions as method if first argument is a pointer to struct
    * Method use original c argument names
    * Method has the origin c docstring
    * Method has a short name removing the object name and the library namespace
    * enum values are now scoped inside an enum class
    * enum values have shorter names since name clashing cannot happen anymore
    * rewrites function that takes pointer arguments to return multiple values
    """
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
        self.new_code = []
        self.names = Trie()
        self.rename_types = dict()
        self.current_class_name = None

    def post_process_class_defintion(self, class_def: T.ClassDef):
        """Make a final pass over the generated class to improve function names"""

        class_name = class_def.name.lower()
        names = defaultdict(int)

        for expr in class_def.body:
            if not isinstance(expr, T.FunctionDef):
                continue

            for n in expr.name.split('_'):
                if len(n) > 0:
                    names[n] += 1

        names = list(names.items())

        # remove names that are not used that often
        names = sorted(filter(lambda x: x[1] > 2, names), key=lambda x: x[1])

        # this is the magic filter that makes thing work
        # by forcing the name we are removing to be part of the type name
        # we are almost sure to remove duplicated data that is not useful
        # even when it appears multiple times it can make sense to have it duplicated
        # Example:
        #   read_le16, read_le32, read_le64
        #   write_le16, write_le32, write_le64

        names = list(map(lambda x: x[0], filter(lambda x: x[0] in class_name, names)))

        for expr in class_def.body:
            if not isinstance(expr, T.FunctionDef):
                continue

            for useless_name in names:
                expr.name = clean_name(expr.name, useless_name)

    def group_constant_to_enums(self):
        pass

    def clean_up_enumeration(self, class_def: T.ClassDef):
        _, names = parse_sdl_name(class_def.name)
        cl_name = class_name(*names)

        # make a short alias of the enum (without the hardcoded c namespace)
        if cl_name != class_def.name:
            self.new_code.append((None, T.Assign([T.Name(cl_name)], T.Name(class_def.name))))

        t = Trie()
        counts = 0
        for expr in class_def.body:
            if match(expr, 'Assign') and match(expr.targets[0], 'Name'):
                constant_name = expr.targets[0].id
                t.insert(constant_name)
                counts += 1

        _ = list(t.redundant_prefix())
        if len(_) > 1:
            # select the shortest prefix that is common to all
            most_likely = _[0]
            for c, n in _:

                if len(n) < len(most_likely[1]):
                    most_likely = (c, n)

            # check that the prefix is common to all
            good = True
            for c, n in _:
                if not most_likely[1] in n:
                    good = False
                    break

            if good:
                _ = [most_likely]
            else:
                _ = []

        if len(_) == 1:
            c, namespace = _[0]

            # SDL insert a None/Max enum that does not follow the pattern
            if counts != c + 1:
                return class_def

            for expr in class_def.body:
                if match(expr, 'Assign') and match(expr.targets[0], 'Name'):
                    constant_name = expr.targets[0].id
                    expr.targets[0].id = clean_name(constant_name, namespace)

        return class_def

    def fetch_docstring(self, data: T.ClassDef):
        if match(data.body[0], 'Constant') and data.body[0].docstring:
            return data.body.pop(0)
        return None

    def class_definition(self, class_def: T.ClassDef, depth):
        self.ctypes[class_def.name] = class_def

        # Opaque struct: move on
        if class_def.name[0] == '_':
            return class_def

        self_wrap = self.wrappers.get(class_def.name)
        if self_wrap is None:
            if T.Name('enumeration') in class_def.decorator_list:
                return self.clean_up_enumeration(class_def)

            _, names = parse_sdl_name(class_def.name)
            docstring = self.fetch_docstring(class_def)

            cl_name = class_name(*names)
            self_wrap = T.ClassDef(cl_name)
            self.new_code.append((class_def.name, self_wrap))
            self.wrappers[class_def.name] = self_wrap
            self.wrappers_2_ctypes[self_wrap.name] = class_def.name
            self.wrapper_order[self_wrap.name] = len(self.wrappers)

            if docstring:
                self_wrap.body.append(docstring)
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

        arg_names = get_kwarg_arg('arg_names', call.keywords, None)
        docstring = get_kwarg_arg('docstring', call.keywords, '')

        # the data is now duplicated in our better api
        # we can just remove it
        call.keywords = []

        if arg_names is not None:
            arg_names = [a.value.lower() for a in arg_names.elts]
        else:
            arg_names = self.ARGS

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
        arg_names = list(arg_names[1:])
        self.current_class_name = self_wrap.name

        if docstring:
            # increase the indentation
            docstring.value = docstring.value.replace('\n    ',  '\n        ')

        new_fun = T.FunctionDef(function_name(*names))
        new_fun.returns = self.rename(ctype_return)
        new_fun.args = T.Arguments(args=[T.Arg('self')] + [T.Arg(n, self.rename(t)) for n, t in zip(arg_names, ctype_args)])

        # we need to convert the result to our new class
        ccall = T.Call(T.Name(fun_name), [self.SELF_HANDLE] + [T.Name(arg_names[i]) for i in range(len(ctype_args))])

        # does the return type need to be wrapped
        if new_fun.returns != ctype_return:
            cast_to = new_fun.returns

            if isinstance(new_fun.returns, T.Constant):
                cast_to = T.Name(new_fun.returns.value)

            ccall = T.Call(T.Attribute(cast_to, 'from_handle'), [ccall])

        new_fun.body = []
        if docstring:
            new_fun.body.append(T.Expr(docstring))
        new_fun.body.append(T.Return(ccall))

        if self.is_multi_output(new_fun):
            new_fun = self.rewrite_multi_output_function(new_fun)

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

    def is_multi_output(self, func: T.FunctionDef):
        expr = func.body[0]

        if not match(expr, 'Expr', ('value', 'Constant')):
            return False

        expr: T.Constant = func.body[0].value

        if not expr.docstring:
            return False

        # if doc string specify it returns an error
        # or if function is known to return nothing
        if ':return 0 on success, or -1' not in expr.value and (match(func.returns, 'Name') and func.returns.id != 'None'):
            return False

        for arg in func.args.args[1:]:
            if not match(arg.annotation, 'Call', ('func', 'Name')):
                return False

            elif arg.annotation.func.id != 'POINTER':
                return False

        return True

    def rewrite_multi_output_function(self, func: T.FunctionDef):
        new_func = T.FunctionDef(func.name)
        new_func.args = T.Arguments(args=[T.Arg('self')])
        new_func.body = [func.body[0]]

        arg_len = len(func.args.args[1:])
        if arg_len == 0:
            return func

        for arg in func.args.args[1:]:
            # Generate the result argument
            var_type = arg.annotation.args[0]
            new_func.body.append(T.Assign([T.Name(arg.arg)], T.Call(var_type)))

        original_call: T.Call = func.body[1].value

        for i in range(len(original_call.args[1:])):
            original_call.args[i + 1] = T.Call(T.Name('byref'), [T.Name(func.args.args[i + 1].arg)])

        new_func.body.append(T.Assign([T.Name('error')], original_call))

        returns = [T.Name(arg.arg) for arg in func.args.args[1:]]
        if len(returns) == 1:
            new_func.body.append(T.Return(returns[0]))
        else:
            new_func.body.append(T.Return(T.Tuple(returns)))

        return new_func

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
        for k, v in self.new_code:
            if isinstance(v, T.ClassDef):
                if self.wrapper_method_count.get(v.name, 0) > 0:
                    self.post_process_class_defintion(v)
                    module.body.append(v)

                elif v.name in self.wrappers_2_ctypes:
                    c_struct = self.wrappers_2_ctypes.get(v.name)
                    # make it an alias for the ctype
                    module.body.append(T.Expr(T.Assign([T.Name(v.name)], T.Name(c_struct))))
            else:
                module.body.append(T.Expr(v))

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


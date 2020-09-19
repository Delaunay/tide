import ast
from ast import Module
from dataclasses import dataclass
import logging
import re
from typing import List

from astunparse import unparse, dump
import clang.cindex
from clang.cindex import Cursor, CursorKind, Type, SourceLocation, TypeKind, Token


from tide.generators.api_generators import get_comment, type_mapping
from tide.generators.clang_utils import parse_c_expression_recursive
from tide.generators.debug import show_elem, traverse, d
from tide.generators.operator_precedence import is_operator, TokenParser, UnsupportedExpression
import tide.generators.nodes as T


# empty_line = re.compile(r'((\r\n|\n|\r)$)|(^(\r\n|\n|\r))|^\s*$', re.MULTILINE)
empty_line = re.compile(r'^\s*$', re.MULTILINE)
c_identifier = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
log = logging.getLogger('TIDE')


@dataclass
class MacroDefinition:
    name: str
    args: List[str]
    tokens: List[str]


def is_valid(name):
    # flag something like below as invalid
    # union SDL_GameControllerButtonBind::(anonymous at /usr/include/SDL2/SDL_gamecontroller.h:75:5)
    return not all(c in name for c in (':', '(', '.', ' '))


def get_typename(type: Type) -> T.Name:
    if not type.is_const_qualified():
        return T.Name(type.spelling)

    typename = type.spelling.replace('const ', '')
    return T.Name(typename)


def compact(string):
    return empty_line.sub('', string)


class Unsupported(Exception):
    pass


class _Token:
    def __init__(self, a):
        self.spelling = a

    def __repr__(self):
        return f'\'{self.spelling}\''


def to_tokens(*args):
    return [_Token(a) for a in args]


def to_string(*args):
    return [a.spelling for a in args]


# it is hard to know if we have a `callable` macro or not
# in C/C++ the difference is a space between the defined name and the parenthesis
# but Clang erase all superfluous space so we cannot know right away
def parse_macro(tokens):
    """

    Examples
    --------
    with arguments
    >>> toks = to_tokens(
    ...     'SDL_reinterpret_cast', '(', 'type', ',', 'expression', ')',
    ...     '(', '(', 'type', ')', '(', 'expression', ')', ')'
    ... )
    >>> name, args, body = parse_macro(toks)
    >>> name.spelling
    'SDL_reinterpret_cast'
    >>> list(args)
    ['type', 'expression']
    >>> list(body)
    ['(', '(', 'type', ')', '(', 'expression', ')', ')']

    Ambigous
    >>> toks = to_tokens(
    ...     'SDL_IN_BYTECAP', '(', 'x', ')'
    ... )
    >>> name, args, body = parse_macro(toks)
    >>> name.spelling
    'SDL_IN_BYTECAP'
    >>> list(args)
    ['x']
    >>> list(body)
    []

    """
    name = tokens[0]
    args = []

    i = 0

    if len(tokens) > 1 and tokens[1].spelling == '(':
        if tokens[2].spelling == ')':
            return name, [], list(tokens[3:])

        i = 2
        tok = tokens[i]
        while tok.spelling != ')':
            if tok.spelling != ',':
                # argument is not an identifier
                if re.match(c_identifier, tok.spelling) is not None:
                    args.append(tok)
                else:
                    log.debug(f'{tok.spelling} not an identifier')
                    return name, [], list(tokens[1:])

            i += 1
            tok = tokens[i]

    # arguments should be used in the body
    # else we think it is a macro without arg
    body = list(tokens[i + 1:])

    # empty macro
    # happens often enough
    if len(body) == 0:
        return name, args, body

    for arg in reversed(args):
        for b in body:
            if arg.spelling == b.spelling:
                break
        else:
            log.debug(f'argument unused {arg.spelling} {body}')
            return name, [], list(tokens[1:])

    if len(args) == 0:
        return name, [], list(tokens[1:])

    return name, args, body


def parse_macro2(name, args, body: List[Token], definitions=None, registry=None):
    parser = TokenParser(body, definitions, registry)
    expr = parser.parse_expression()

    return expr


def sorted_children(cursor):
    """Because macros are processed first we have have issues when transforming them to functions
    so we need to insert them in their right position in a kind of stable merge kind of operation.
    This does not guarantee macros to work because in C they can be defined earlier than the entities they used
    although in practice they should be close

    This also allow us to group Macro and their definitions.
    For example is is often the case that function definition have additional attributes prepended through macros.
    """
    def is_builtin(elem):
        return elem.location.file is None

    def is_not_builtin(elem):
        return not is_builtin(elem)

    elements = list(filter(is_not_builtin, cursor.get_children()))
    builtin = list(filter(is_builtin, cursor.get_children()))

    def is_macro(elem):
        return elem.kind in (CursorKind.MACRO_DEFINITION, CursorKind.MACRO_INSTANTIATION, CursorKind.INCLUSION_DIRECTIVE)

    def not_macro(elem):
        return not is_macro(elem)

    file_order = dict()
    for e in elements:
        if e.location.file.name not in file_order:
            file_order[e.location.file.name] = len(file_order)

    #
    macros = list(filter(is_macro, reversed(elements)))
    not_macros = list(filter(not_macro, reversed(elements)))

    assert len(elements) > 0
    assert len(macros) + len(not_macros) == len(elements)

    merged = []

    def pop(array):
        if len(array) > 0:
            return array.pop()

    macro = pop(macros)
    expr = pop(not_macros)

    while len(not_macros) > 0 or len(macros) > 0 or expr is not None or macro is not None:
        # dump the remaining macros/expr
        if expr is None and macro is not None:
            merged.append(macro)
            macro = pop(macros)

        elif macro is None and expr is not None:
            merged.append(expr)
            expr = pop(not_macros)

        elif macro.location.file.name != expr.location.file.name:
            macro_file = file_order[macro.location.file.name]
            expr_file = file_order[expr.location.file.name]

            if macro_file > expr_file:
                merged.append(macro)
                macro = pop(macros)
            else:
                merged.append(expr)
                expr = pop(not_macros)

        elif macro.location.file.name == expr.location.file.name:
            if macro.location.line > expr.location.line:
                merged.append(expr)
                expr = pop(not_macros)
            else:
                merged.append(macro)
                macro = pop(macros)

        else:
            raise RuntimeError()

    assert len(merged) == len(elements)
    return merged, builtin


class BindingGenerator:
    """Generate C to python bindings given library headers
    This generate a verbatim translation of the library the result is far from pythonic

    The API generator pass can later be applied to the result to generate a more organized version
    """

    def __init__(self):
        self.type_registry = type_mapping()
        # keep track of all the macros we cannot support
        # so other macros using those will be me ignored as well
        self.unsupported_macros = set()
        # definition are macro/value defined at compile time
        # those definition in particular are Compiler builtin
        # this is so we can do our own macro expansion when required
        self.definitions = dict()
        self.dispatcher = {
            # Declarations
            CursorKind.FUNCTION_DECL: self.generate_function,
            CursorKind.STRUCT_DECL: self.generate_struct_union,
            CursorKind.UNION_DECL: self.generate_struct_union,
            CursorKind.TYPEDEF_DECL: self.generate_typedef,
            CursorKind.ENUM_DECL: self.generate_enum,

            # Operations
            CursorKind.UNARY_OPERATOR: self.generate_unary_operator,
            CursorKind.BINARY_OPERATOR: self.generate_binary_operator,
            CursorKind.CSTYLE_CAST_EXPR: self.generate_c_cast,
            CursorKind.VAR_DECL: self.generate_var_decl,

            # Useless
            CursorKind.UNEXPOSED_EXPR: self.ignore,
            CursorKind.PAREN_EXPR: self.ignore,

            # Leaves
            CursorKind.TYPE_REF: self.generate_typeref,
            CursorKind.DECL_REF_EXPR: self.generate_typeref,
            CursorKind.INTEGER_LITERAL: self.generate_integer,
            CursorKind.FLOATING_LITERAL: self.generate_float,
            CursorKind.STRING_LITERAL: self.generate_string,

            # Macros
            CursorKind.INCLUSION_DIRECTIVE: self.generate_include,
            CursorKind.MACRO_INSTANTIATION: self.generate_macro_instantiation,
            CursorKind.MACRO_DEFINITION: self.generate_macro_definition,
        }

    def generate_var_decl(self, elem, **kwargs):
        return T.AnnAssign(T.Name(elem.spelling), self.generate_type(elem.type), None)

    def ignore(self, elem, **kwargs):
        children = list(elem.get_children())
        assert len(children) == 1
        return self.dispatch(children[0], **kwargs)

    def generate_typeref(self, elem, **kwargs):
        return T.Name(elem.spelling)

    def generate_typedef(self, elem, **kwargs):
        """Generate a type alias

        Examples
        --------
        >>> from tide.generators.clang_utils import parse_clang
        >>> tu, index = parse_clang('typedef int int32;')
        >>> module = BindingGenerator().generate(tu)
        >>> print(compact(unparse(module)))
        <BLANKLINE>
        int32 = c_int
        <BLANKLINE>
        """
        t1 = elem.type
        t2 = elem.underlying_typedef_type

        log.debug(f'Typedef {t1.spelling} = {t2.spelling}')
        # SDL_version = struct SDL_version
        if t1.spelling == t2.spelling.split(' ')[-1]:
            if t2.spelling not in self.type_registry:
                self.type_registry[t2.spelling] = T.Name(t1.spelling, ctx=ast.Load())
            return None

        t2type: T.Name = self.generate_type(t2)
        if t2.spelling not in self.type_registry:
            self.type_registry[t2.spelling] = T.Name(t1.spelling, ctx=ast.Load())

        expr = ast.Assign([T.Name(t1.spelling, ctx=ast.Store())], t2type)
        return expr

    def generate_type(self, type, depth=0):
        if type.spelling == 'va_list':
            raise Unsupported()

        lookup_name = type.spelling
        if type.is_const_qualified():
            lookup_name = lookup_name.replace('const', '').strip()

        # This is meant to remember typedefs and use the typedef instead of the underlying type
        # In particular when `typedef struct` is used
        cached_type = self.type_registry.get(lookup_name)
        if cached_type is not None:
            log.debug(f'{d(depth)}Found cached type `{cached_type}`')
            return cached_type

        val = self._generate_type(type, depth)
        self.type_registry[type.spelling] = val
        log.debug(f'{d(depth)}Resolved type `{type.spelling}` to `{val}`')
        return val

    def _generate_type(self, type: Type, depth=0):
        # print(type.kind, type.spelling, self.type_registry.get(type.spelling, 'NOT FOUND'))
        if type.kind == TypeKind.VOID:
            return T.Name('None')

        if type.kind == TypeKind.INT:
            return T.Name('c_int')

        if type.kind == TypeKind.POINTER and type.get_pointee().kind == TypeKind.VOID:
            return T.Name('c_void_p')

        if type.kind == TypeKind.POINTER and type.get_pointee().kind == TypeKind.CHAR_S:
            return T.Name('c_char_p')

        if type.kind == TypeKind.POINTER:
            pointee: Type = type.get_pointee()

            # Typedef use the name that it is aliased to
            if pointee.kind is TypeKind.TYPEDEF:
                pointee = get_typename(pointee)

            elif pointee.kind != TypeKind.VOID:
                pointee = self.generate_type(pointee, depth + 1)
            else:
                pointee = T.Name('c_void_p')

            # Function pointer do not need to be decorated by POINTER call
            if isinstance(pointee, T.Call) and isinstance(pointee.func, T.Name) and pointee.func.id == 'CFUNCTYPE':
                return pointee

            # for native types we need to keep ref because python will copy them
            return T.Call(T.Name('POINTER'), [pointee])

        if type.kind == TypeKind.CHAR_S:
            return T.Name('c_char_p')

        # if type.is_const_qualified():
        #     return T.Name(get_typename(type))

        if type.kind == TypeKind.TYPEDEF:
            return get_typename(type)

        if type.kind == TypeKind.FUNCTIONPROTO or (type.kind == TypeKind.UNEXPOSED and type.get_canonical().kind == TypeKind.FUNCTIONPROTO):
            # SDL_HitTest = CFUNCTYPE(SDL_HitTestResult, POINTER(SDL_Window), POINTER(SDL_Point), c_void_p)
            canon = type
            if type.kind == TypeKind.UNEXPOSED:
                canon = type.get_canonical()

            rtype = canon.get_result()

            args = []
            for arg in canon.argument_types():
                args.append(self.generate_type(arg, depth + 1))

            returntype = self.generate_type(rtype, depth + 1)

            cargs = [returntype]
            cargs.extend(args)
            return T.Call(T.Name('CFUNCTYPE'), args=cargs)

        if type.kind == TypeKind.CONSTANTARRAY:
            t = self.generate_type(type.element_type, depth + 1)
            return T.BinOp(t, ast.Mult(), T.Constant(type.element_count))

        # Represents a C array with an unspecified size.
        if type.kind == TypeKind.INCOMPLETEARRAY:
            element_type = self.generate_type(type.element_type, depth + 1)
            # char *[] -> char **
            return T.Call(T.Name('POINTER'), [element_type])

        # struct <TYPENAME>
        if type.kind == TypeKind.ELABORATED:
            return T.Name(get_typename(type).id.replace('struct', '').strip())

        if type.kind == TypeKind.ENUM:
            return get_typename(type)

        # print('gentype')
        show_elem(type, print_fun=log.debug)
        return get_typename(type)

    def generate_function(self, elem: Cursor, depth=0, **kwargs):
        """Generate a type alias

        Examples
        --------
        >>> from tide.generators.clang_utils import parse_clang
        >>> tu, index = parse_clang('float add(float a, float b);')
        >>> module = BindingGenerator().generate(tu)
        >>> print(compact(unparse(module)))
        <BLANKLINE>
        add = _bind('add', [c_float, c_float], c_float)
        <BLANKLINE>
        """
        log.debug(f'{d(depth)}Generate function `{elem.spelling}`')
        definition: Cursor = elem.get_definition()

        if definition is None:
            definition = elem

        rtype = self.generate_type(definition.result_type, depth + 1)
        args = definition.get_arguments()

        pyargs = []
        for a in args:
            atype = self.generate_type(a.type, depth + 1)
            pyargs.append(atype)

        funnane = definition.spelling
        if not pyargs:
            pyargs = T.Name('None')
        else:
            pyargs = T.List(elts=pyargs)

        binding_call = T.Call(T.Name('_bind'), [T.Str(funnane), pyargs, rtype])
        return T.Assign([T.Name(funnane)], binding_call)

    def get_name(self, elem, rename=None, depth=0):
        # log.debug(f'{d(depth)}Fetch name')
        pyname = elem.spelling

        if hasattr(elem, 'displayname') and elem.displayname:
            pyname = elem.displayname

        # Typedef or anonymous struct/union
        if not pyname:
            pyname = elem.type.spelling

        if rename is not None and hasattr(elem, 'get_usr') and elem.get_usr() in rename:
            parent, name = rename[elem.get_usr()]
            return name

        if not is_valid(pyname):
            pyname = ''

        return pyname

    def find_anonymous_fields(self, elem, parent='', depth=0):
        # Find Anonymous struct or union
        # to rename them so something valid
        # Those are also nested struct
        anonymous = dict()
        anonymous_renamed = dict()

        for attr in elem.get_children():
            if attr.kind == CursorKind.UNION_DECL or attr.kind == CursorKind.STRUCT_DECL:
                attr_type_name = self.get_name(attr, depth=depth + 1)
                log.debug(f'{d(depth)}Found nested decl, {attr.kind} {attr.spelling} {attr_type_name}')
                anonymous[attr.get_usr()] = attr

            if attr.kind == CursorKind.FIELD_DECL:
                usr = self.get_underlying_type_uid(attr.type)
                log.debug(f'{d(depth)} attr, {attr.kind} {attr.spelling} {usr}')

                if usr in anonymous:
                    log.debug(f'{d(depth)}Found attribute using nested decl: {attr.kind} {attr.spelling}')

                    name = '_' + self.get_name(attr, depth=depth + 1).capitalize()
                    anonymous_renamed[usr] = (parent, name)

        return anonymous_renamed

    def get_underlying_type_uid(self, type: Type):
        if type.kind == TypeKind.POINTER:
            return self.get_underlying_type_uid(type.get_pointee())

        if type.kind == TypeKind.TYPEDEF:
            return type.get_declaration().get_usr()

        if type.kind == TypeKind.ELABORATED:
            show_elem(type)
            print(type.get_declaration().get_usr())
            return type.get_declaration().get_usr()

        return type.get_declaration().get_usr()

    def generate_field(self, body, attrs, attr, anonymous_renamed, depth, **kwargs):
        if attr.kind == CursorKind.FIELD_DECL:
            # Rename anonymous types
            uid = self.get_underlying_type_uid(attr.type)

            log.debug(f'{d(depth)}uid: {uid} {attr.type.spelling} {anonymous_renamed}')
            if uid in anonymous_renamed:
                parent, name = anonymous_renamed[uid]
                if parent:
                    typename = T.Attribute(T.Name(parent), name)
                else:
                    typename = T.Name(name)

                if attr.type.kind == TypeKind.POINTER:
                    typename = T.Call(T.Name('POINTER'), [typename])
            else:
                typename = self.generate_type(attr.type, depth + 1)

            pair = T.Tuple()
            pair.elts = [
                T.Str(attr.spelling),
                typename
            ]
            attrs.elts.append(pair)

        elif attr.kind in (CursorKind.UNION_DECL, CursorKind.STRUCT_DECL):
            nested_struct = self.generate_struct_union(
                attr,
                depth + 1,
                nested=True,
                rename=anonymous_renamed)

            body.append(nested_struct)
        elif attr.kind == CursorKind.PACKED_ATTR:
            for attr2 in attr.get_children():
                self.generate_field(body, attrs, attr2, anonymous_renamed, depth + 1)
                # attrs.append(field)
        else:
            show_elem(attr)
            print('NESTED ', attr.kind)
            raise RuntimeError('')

    def generate_struct_union(self, elem: Cursor, depth=1, nested=False, rename=None, **kwargs):
        """Generate a struct or union alias

        Examples
        --------
        >>> from tide.generators.clang_utils import parse_clang
        >>> tu, index = parse_clang('struct Point { float x, y;};')
        >>> module = BindingGenerator().generate(tu)
        >>> print(compact(unparse(module)))
        <BLANKLINE>
        class Point(Structure):
            pass
        <BLANKLINE>
        Point._fields_ = [('x', c_float), ('y', c_float)]
        <BLANKLINE>


        >>> from tide.generators.clang_utils import parse_clang
        >>> tu, index = parse_clang('union Point { float x; int y;};')
        >>> module = BindingGenerator().generate(tu)
        >>> print(compact(unparse(module)))
        <BLANKLINE>
        class Point(Union):
            pass
        <BLANKLINE>
        Point._fields_ = [('x', c_float), ('y', c_int)]
        <BLANKLINE>
        """

        log.debug(f'{d(depth)}Generate struct `{elem.spelling}`')
        pyname = self.get_name(elem, rename=rename, depth=depth + 1)

        base = 'Structure'
        if elem.kind == CursorKind.UNION_DECL:
            base = 'Union'

        # For recursive data structure
        #  log.debug(pyname)
        self.type_registry[f'struct {pyname}'] = T.Name(pyname)
        self.type_registry[f'const struct {pyname}'] = T.Name(pyname)

        parent = pyname
        anonymous_renamed = self.find_anonymous_fields(elem, parent, depth=depth + 1)

        # Docstring is the first element of the body
        # T.Constant(get_comment(elem))
        body = []
        attrs = T.List()

        attr: Cursor
        for attr in elem.get_children():
            self.generate_field(body, attrs, attr, anonymous_renamed, depth)

        # fields are at the end because we might use types defined above
        if not body:
            body.append(ast.Pass())

        if not attrs.elts:
            return T.ClassDef(name=pyname, bases=[T.Name(base)], body=body)

        fields = T.Assign([T.Attribute(T.Name(pyname), '_fields_')], attrs)
        return [T.ClassDef(name=pyname, bases=[T.Name(base)], body=body), fields]

    def generate_enum(self, elem: Cursor, depth=0, **kwargs):
        """ Generate a enum

        Examples
        --------
        >>> from tide.generators.clang_utils import parse_clang
        >>> tu, index = parse_clang('enum Colors { Red, Green, Blue;};')
        >>> module = BindingGenerator().generate(tu)
        >>> print(compact(unparse(module)))
        <BLANKLINE>
        Colors = c_int
        <BLANKLINE>
        Red = 0
        <BLANKLINE>
        Green = 1
        <BLANKLINE>
        Blue = 2
        <BLANKLINE>
        """
        log.debug(f'{d(depth)}Generate Enum')
        name = self.get_name(elem)

        enum = []

        if name:
            enum.append(T.Assign([T.Name(name)], self.type_registry.get('int')))

        for value in elem.get_children():
            if value.kind == CursorKind.ENUM_CONSTANT_DECL:
                enum.append(T.Assign(
                    [T.Name(self.get_name(value))],
                    T.Constant(value.enum_value)))
            else:
                log.error(f'Unexpected children {value.kind}')
                raise RuntimeError()

        return enum

    def generate_include(self, elem: Cursor, **kwargs):
        log.debug(f'including f{elem.spelling}')

    def generate_macro_instantiation(self, elem: Cursor, **kwargs):
        return None

        # macro_definition = elem.get_definition()
        # if macro_definition is not None and macro_definition.location.file is None:
        #     return
        #
        # log.debug(f'Macro call {elem.spelling}')
        # # show_elem(elem)
        # args = list(elem.get_arguments())
        # children = list(elem.get_children())
        #
        # if len(args) != 0:
        #     for arg in args:
        #         show_elem(arg)
        #         assert False
        #
        # if len(children) != 0:
        #     for child in children:
        #         show_elem(child)
        #         assert False

        # return T.Name(elem.spelling)

    @staticmethod
    def is_identifier(x: str):
        if not x.isalpha():
            return False

        if x.isalnum():
            return True

    def generate_macro_definition(self, elem: Cursor, **kwargs):
        """Transform a macro into a function if possible

        Examples
        --------
        >>> from tide.generators.clang_utils import parse_clang
        >>> tu, index = parse_clang('#define PI 3.14')
        >>> module = BindingGenerator().generate(tu)
        >>> print(compact(unparse(module)))
        <BLANKLINE>
        PI = 3.14
        <BLANKLINE>

        >>> tu, index = parse_clang(''
        ... '#define SDL_AUDIO_ALLOW_FREQUENCY_CHANGE    0x00000001\\n'
        ... '#define SDL_AUDIO_ALLOW_FORMAT_CHANGE       0x00000002\\n'
        ... '#define SDL_AUDIO_ALLOW_CHANNELS_CHANGE     0x00000004\\n'
        ... '#define SDL_AUDIO_ALLOW_ANY_CHANGE          (SDL_AUDIO_ALLOW_FREQUENCY_CHANGE|SDL_AUDIO_ALLOW_FORMAT_CHANGE|SDL_AUDIO_ALLOW_CHANNELS_CHANGE)\\n'
        ... )
        >>> module = BindingGenerator().generate(tu)
        >>> print(compact(unparse(module)))
        <BLANKLINE>
        SDL_AUDIO_ALLOW_FREQUENCY_CHANGE = 1
        <BLANKLINE>
        SDL_AUDIO_ALLOW_FORMAT_CHANGE = 2
        <BLANKLINE>
        SDL_AUDIO_ALLOW_CHANNELS_CHANGE = 4
        <BLANKLINE>
        SDL_AUDIO_ALLOW_ANY_CHANGE = (SDL_AUDIO_ALLOW_FREQUENCY_CHANGE | (SDL_AUDIO_ALLOW_FORMAT_CHANGE | SDL_AUDIO_ALLOW_CHANNELS_CHANGE))
        <BLANKLINE>
        """
        # builtin macros
        if elem.location.file is None:
            return

        log.debug(f'Macro definition {elem.spelling}')

        args = list(elem.get_arguments())
        children = list(elem.get_children())
        tokens = list(elem.get_tokens())

        if len(args) != 0:
            for arg in args:
                show_elem(arg, print_fun=log.debug)
                assert False

        if len(children) != 0:
            for child in children:
                show_elem(child, print_fun=log.debug)
                assert False

        if len(tokens) == 1:
            return

        name, tok_args, tok_body = parse_macro(tokens)

        if len(tok_body) == 0:
            return

        if name.spelling == 'NULL':
            return T.Assign([T.Name('NULL')], T.Name('None'))

        try:
            bods = {t.spelling for t in tok_body}
            if not bods.isdisjoint(self.unsupported_macros):
                raise UnsupportedExpression()

            py_body = parse_macro2(name, tok_args, tok_body, self.definitions, self.type_registry)

        except UnsupportedExpression:
            self.unsupported_macros.add(name.spelling)
            body = [b.spelling for b in tok_body]
            log.warning(f'Unsupported expression, cannot transform macro {name} {"".join(body)}')
            return

        name = name.spelling

        # if name == 'SDL_TOUCH_MOUSEID':
        #     print(py_body)
        #     assert False

        if len(tok_args) == 0 and not isinstance(py_body, T.If):
            return T.Assign([T.Name(name)], py_body)

        func = T.FunctionDef(
            name,
            T.Arguments(args=[T.Arg(arg=a.spelling) for a in tok_args])
        )

        if isinstance(py_body, T.Expr):
            py_body = py_body.value

        # we use ifs as a makeshift Body expression
        if isinstance(py_body, T.If) and isinstance(py_body.test, T.Constant) \
                and py_body.test.value is True:
            func.body = py_body.body
        else:
            func.body = [
                T.Return(py_body)
            ]

        return func

    def generate_c_cast(self, elem, **kwargs):
        show_elem(elem)
        children = list(elem.get_children())

        if len(children) == 2:
            type, expr = children
            traverse(type, print_fun=log.debug)
            traverse(expr, print_fun=log.debug)

            typecast = self.dispatch(type, **kwargs)
            if isinstance(typecast, str):
                typecast = T.Name(typecast)

            return T.Call(typecast, [self.dispatch(expr, **kwargs)])

        if len(children) == 1:
            return self.dispatch(children[0], **kwargs)

        return None

    def generate_integer(self, elem: Cursor, **kwargs):
        try:
            val = list(elem.get_tokens())[0].spelling

            val = val.replace('u', '')
            val = val.replace('ll', '')
            val = val.replace('U', '')
            val = val.replace('L', '')

            base = 10
            if '0x' in val:
                base = 16

            return T.Constant(int(val, base=base))
        except IndexError:
            # this integer comes from __LINE__ macro
            # this is not correct at all, this should return the line on which it is called
            # but we cannot really do that in python I think
            return T.Constant(int(elem.location.line))

    def generate_string(self, elem, **kwargs):
        return T.Constant(elem.spelling)

    def generate_float(self, elem, **kwargs):
        toks = [t.spelling for t in elem.get_tokens()]
        assert len(toks) == 1
        return T.Constant(float(toks[0]))

    def generate_unary_operator(self, elem, macro_def: MacroDefinition = None, **kwargs):
        expr = list(elem.get_children())
        assert len(expr) == 1

        expr = self.dispatch(expr[0], **kwargs)

        more_toks = None
        if macro_def is not None:
            more_toks = macro_def.tokens

        op_tok = self.fetch_operator(elem, more_toks)

        if op_tok == '-':
            op = T.USub()

        if op_tok == '~':
            op = T.Invert()

        assert op is not None
        return T.UnaryOp(op=op, operand=expr)

    def fetch_operator(self, elem, toks):
        # use tokens to find possible operators
        # get_tokens() is not always populated correctly that is why the parent have to pass down the tokens
        # but it also means the tokens could have more operators than we have

        # ---
        possible_ops = set()
        # use tokens to find possible operators
        # get_tokens() is not always populated correctly that is why the parent have to pass down the tokens
        # but it also means the tokens could have more operators than we have
        if toks is not None:
            log.debug(f'{toks}')
        else:
            toks = [t.spelling for t in elem.get_tokens()]
            log.debug(f'{toks}')

        assert len(toks) > 0

        for t in toks:
            if t in ('(', ')', '[', ']', ','):
                continue

            if is_operator(t):
                possible_ops.add(t)

        log.debug(f'Possible operand from tokens {possible_ops}')

        if len(possible_ops) == 0:
            log.debug('Could not find operand for unary operator expression')
            return None

        if len(possible_ops) > 1:
            # we can use location to determine which token is the most likely operand
            log.debug('FIX ME')
            assert False

        return possible_ops.pop()

    def generate_binary_operator(self, elem, macro_def: MacroDefinition = None, **kwargs):
        exprs = list(elem.get_children())
        assert len(exprs) == 2

        lhs = self.dispatch(exprs[0], macro_def=macro_def, **kwargs)
        rhs = self.dispatch(exprs[1], macro_def=macro_def, **kwargs)

        more_toks = None
        if macro_def is not None:
            more_toks = macro_def.tokens

        op_tok = self.fetch_operator(elem, more_toks)

        op = None
        if op_tok == '<<':
            op = T.LShift()
        elif op_tok == '>>':
            op = T.RShift()
        elif op_tok == '|':
            op = T.BitOr()

        assert op is not None
        return T.BinOp(left=lhs, op=op, right=rhs)

    def dispatch(self, elem, depth=0, **kwargs):
        # log.debug(f'{d(depth)} {elem.kind}')

        fun = self.dispatcher.get(elem.kind, None)
        if fun is None:
            return show_elem(elem, print_fun=log.debug)

        return fun(elem, depth=depth + 1, **kwargs)

    def process_builtin_macros(self, cursor: Cursor):
        tokens = list(cursor.get_tokens())
        name, tok_args, tok_body = parse_macro(tokens)

        if len(tok_body) == 0:
            self.definitions[name.spelling] = T.Constant(True)
            return

        try:
            bods = {t.spelling for t in tok_body}
            if not bods.isdisjoint(self.unsupported_macros):
                raise UnsupportedExpression()

            py_body = parse_macro2(name, tok_args, tok_body)

        except UnsupportedExpression:
            self.unsupported_macros.add(name.spelling)

        self.definitions[name.spelling] = py_body

    def generate(self, tu, guard=None):
        module: T.Module = Module()
        module.body = []

        children, builtin = sorted_children(tu.cursor)

        assert len(builtin) > 0
        # Process every builtin macros
        for b in builtin:
            if b.kind == CursorKind.MACRO_DEFINITION:
                self.process_builtin_macros(b)

        # for k, v in self.definitions.items():
        #      print(k, v)

        # __BYTE_ORDER__ is defined by clang, __BYTE_ORDER is defined by other includes
        self.definitions['__BYTE_ORDER'] = self.definitions['__BYTE_ORDER__']

        log.debug(f'Processing {len(children)} children')
        elem: Cursor
        for elem in children:
            loc: SourceLocation = elem.location

            if loc.file is not None and guard is not None and not str(loc.file.name).startswith(guard):
                continue

            try:
                expr = self.dispatch(elem)

                if expr is not None and not isinstance(expr, str):
                    if isinstance(expr, list):
                        for e in expr:
                            module.body.append(T.Expr(e))
                    else:
                        module.body.append(T.Expr(expr))
            except Unsupported:
                log.debug(elem)
                pass

        return module


def generate_bindings():
    import sys
    logging.basicConfig(stream=sys.stdout)
    log.setLevel(logging.DEBUG)

    index = clang.cindex.Index.create()
    file = '/usr/include/SDL2/SDL.h'
    # file = '/home/setepenre/work/tide/tests/binding/typedef_func.h'
    # file = '/home/setepenre/work/tide/tests/binding/nested_struct.h'
    tu = index.parse(file, options=0x01)

    for diag in tu.diagnostics:
        log.debug(diag.format())

    gen = BindingGenerator()
    module = gen.generate(tu, guard='/usr/include/SDL2')

    log.debug('=' * 80)

    import os
    dirname = os.path.dirname(__file__)

    with open(os.path.join(dirname, '..', '..', 'output', 'sdl2.py'), 'w') as f:
        f.write("""import os\n""")
        f.write("""from tide.runtime.loader import DLL\n""")
        f.write("""from tide.runtime.ctypes_ext import *\n""")
        f.write("""_lib = DLL("SDL2", ["SDL2", "SDL2-2.0"], os.getenv("PYSDL2_DLL_PATH"))\n""")
        f.write("""_bind = _lib.bind_function\n""")
        f.write(unparse(module))


if __name__ == '__main__':
    import sys
    sys.stderr = sys.stdout

    logging.basicConfig(stream=sys.stdout)
    log.setLevel(logging.DEBUG)

    generate_bindings()

    from tide.generators.clang_utils import parse_clang
    tu, index = parse_clang('float add(float a, float b);')
    module = BindingGenerator().generate(tu)
    print(compact(unparse(module)))

    # from tide.generators.clang_utils import parse_clang
    #
    # tu, index = parse_clang('#define PI 3.14')
    #
    # for diag in tu.diagnostics:
    #     print(diag.format())
    #
    # print(list(tu.cursor.get_children()))
    #
    # for i in list(tu.cursor.get_children()):
    #     print(i.kind)
    #
    # module = BindingGenerator().generate(tu)
    #
    # print(unparse(module))


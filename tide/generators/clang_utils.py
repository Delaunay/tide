from typing import Tuple
import re

import clang.cindex
from clang.cindex import TranslationUnit, Index, CursorKind, Cursor


from tide.generators.debug import show_elem, traverse


def is_not_builtin(elem):
    return elem.location.file is not None


def no_builtin(children):
    return filter(is_not_builtin, children)


def parse_clang(code, ext='c', source='temporary_buffer_1234') -> Tuple[TranslationUnit, Index]:
    """Parse C code using clang, returns a translation unit

    Examples
    --------

    >>> tu, index = parse_clang('double add(double a, double b){ return a + b; }')
    >>> for elem in no_builtin(tu.cursor.get_children()):
    ...     print(elem.spelling, elem.kind)
    add CursorKind.FUNCTION_DECL
    """
    fname = f'{source}.{ext}'
    index = clang.cindex.Index.create()
    tu = index.parse(path=fname, unsaved_files=[(fname, code)], options=0x01)
    return tu, index


class ParsingError(Exception):
    pass


def parse_c_expression(expression, include=None, ext='c', source='temporary_buffer_1234', header=None) -> Tuple[Cursor, Cursor, TranslationUnit]:
    """Hack the clang parser to parse a single expression
    This is used to parse macros and generate corresponding function when possible

    Examples
    --------

    >>> from tide.generators.debug import traverse
    >>> expr, type, _ = parse_c_expression('((Sint8)0x7F)', include='SDL2/SDL.h')
    >>> traverse(expr)
    CursorKind.UNEXPOSED_EXPR
     CursorKind.PAREN_EXPR
      CursorKind.CSTYLE_CAST_EXPR
       CursorKind.TYPE_REF
       CursorKind.INTEGER_LITERAL
    >>> traverse(type)
    TypeKind.INT

    When the expression is incorrect None is returned

    >>> from tide.generators.debug import traverse
    >>> expr, type, _ = parse_c_expression('__attribute__((deprecated))', include='SDL2/SDL.h')
    >>> (expr, type)
    (None, None)

    This function can only handle very simple expression.

    >>> expr, type, _ = parse_c_expression('((X) * (X))')
    >>> traverse(expr)
    None
    """
    sources = []
    if include is not None:
        sources.append(f'#include <{include}>')

    if header is None:
        header = ''

    sources.append(f'void fun_023984() {{ {header}; auto x_203234234 = {expression}; }}')
    sources = '\n'.join(sources)

    tu, _ = parse_clang(sources, ext=ext, source=source)
    function = list(tu.cursor.get_children())[-1]

    assert function.kind == CursorKind.FUNCTION_DECL
    assert function.spelling == 'fun_023984'

    children = list(function.get_children())
    child = None

    while len(children) > 0:
        child = children.pop()

        if child.kind == CursorKind.VAR_DECL and child.spelling == 'x_203234234':
            break

        else:
            for c in child.get_children():
                children.append(c)

    if child.spelling != 'x_203234234':
        return None, None, tu

    result_type = child.type
    children = list(child.get_children())

    expr = None
    if len(children) == 1:
        expr = children[0]
    else:
        result_type = None

    return expr, result_type, tu


undeclared_identifier_error = \
    re.compile(r'.*error: use of undeclared identifier \'(?P<identifier>[a-zA-Z_][a-zA-Z0-9_]*)\'')

# Ignore typing info here, because it is possibly fake
missing_type_specifier = \
    re.compile(r'.*warning: type specifier missing, defaults to \'int\'')

# Extract Real Type form implict cast warning
implicit_conversion = \
    re.compile(r'.*warning: implicit conversion from \'(?P<real_type>[a-zA-Z_][a-zA-Z0-9_]*)\' to \'(?P<new_type>[a-zA-Z_][a-zA-Z0-9_]*)\'')


def parse_c_expression_recursive(expression, include=None, ext='c', source='temporary_buffer_1234') -> Tuple[Cursor, Cursor, TranslationUnit]:
    """Try to automatically fix diagnostic issues.
    At the moment only the undeclared identifier is automatically fixed

    Examples
    --------
    >>> from tide.generators.clang_utils import parse_clang
    >>> child, result_type, tu = parse_c_expression_recursive('((X) * (X))')
    >>> traverse(child)
    CursorKind.PAREN_EXPR
     CursorKind.BINARY_OPERATOR
      CursorKind.UNEXPOSED_EXPR
       CursorKind.PAREN_EXPR
        CursorKind.DECL_REF_EXPR
      CursorKind.UNEXPOSED_EXPR
       CursorKind.PAREN_EXPR
        CursorKind.DECL_REF_EXPR
    """

    expr, type, tu = parse_c_expression(expression, include, ext, source)
    undeclared_identifiers = set()

    for diag in tu.diagnostics:
        match = undeclared_identifier_error.match(diag.format())

        if match is not None:
            undeclared_identifiers.add(match.groupdict()['identifier'])

    src = []
    for i in undeclared_identifiers:
        src.append(f'auto {i};')

    head = '\n'.join(src)
    e, t, tu = parse_c_expression(expression, include, ext, source, head)

    type_is_wrong = is_type_wrong(tu)

    if type_is_wrong:
        t = None

    return e, t, tu


def is_type_wrong(tu):
    for diag in tu.diagnostics:
        match = missing_type_specifier.match(diag.format())
        if match is not None:
            return True

        match = implicit_conversion.match(diag.format())
        if match is not None:
            return True

    return False


def extract_type(tu):
    types = []

    for diag in tu.diagnostics:
        match = implicit_conversion.match(diag.format())

        if match is not None:
            types.add(match.groupdict()['real_type'])

    return types


if __name__ == '__main__':
    child, result_type, tu = parse_c_expression_recursive('((X) * (X))')

    for diag in tu.diagnostics:
        print(diag.format())

    traverse(child)
    traverse(result_type)


    # expr, type = parse_c_expression('((Sint8)0x7F)', include='SDL2/SDL.h')
    #
    # traverse(expr)
    # traverse(type)




    # fun = list(tu.cursor.get_children())[-1]
    #
    # show_elem(fun)
    #
    # for child in fun.get_children():
    #     show_elem(child)
    #
    #     assert child.kind == CursorKind.COMPOUND_STMT
    #     child2 = list(child.get_children())[0]
    #     show_elem(child2)
    #
    #     assert child2.kind == CursorKind.DECL_STMT
    #     child3 = list(child2.get_children())[0]
    #     show_elem(child3)
    #
    #     assert child3.kind == CursorKind.VAR_DECL
    #     name = child3.spelling
    #     assert name == 'x'
    #
    #     child4 = list(child3.get_children())[0]
    #     assert child4.kind == CursorKind.UNEXPOSED_EXPR
    #
    #     child5 = list(child4.get_children())[0]
    #     assert child5.kind == CursorKind.PAREN_EXPR
    #
    #     child6 = list(child5.get_children())[0]
    #     assert child6.kind == CursorKind.CSTYLE_CAST_EXPR
    #
    #     type, expr = list(child6.get_children())
    #     assert type.kind == CursorKind.TYPE_REF
    #     assert type.spelling == 'Sint8'
    #
    #     assert expr.kind == CursorKind.INTEGER_LITERAL
    #     print(list(expr.get_tokens())[0].spelling)

        # def eval(self):
        #     res = conf.lib.clang_Cursor_Evaluate(self)
        #     v = conf.lib.clang_EvalResult_getAsInt(res)
        #     return v

        # print(child4)
        # show_elem(child4)


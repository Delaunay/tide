from typing import Tuple

import clang.cindex
from clang.cindex import TranslationUnit, Index, CursorKind, Cursor


from tide.generators.debug import show_elem, traverse


def parse_clang(code, ext='c', source='string') -> Tuple[TranslationUnit, Index]:
    """Parse C code using clang, returns a translation unit

    Examples
    --------

    >>> tu, index = parse_clang('double add(double a, double b){ return a + b; }')
    >>> for elem in tu.cursor.get_children():
    ...     print(elem.spelling, elem.kind)
    add CursorKind.FUNCTION_DECL
    """
    fname = f'{source}.{ext}'
    index = clang.cindex.Index.create()
    tu = index.parse(path=fname, unsaved_files=[(fname, code)])
    return tu, index


class ParsingError(Exception):
    pass


def parse_c_expression(expression, include=None, ext='c', source='string') -> Tuple[Cursor, Cursor]:
    """Hack the clang parser to parse a single expression
    This is used to parse macros and generate corresponding function when possible

    Examples
    --------

    >>> from tide.generators.debug import traverse
    >>> expr, type = parse_c_expression('((Sint8)0x7F)', include='SDL2/SDL.h')
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
    >>> expr, type = parse_c_expression('__attribute__((deprecated))', include='SDL2/SDL.h')
    None, None
    """
    sources = []
    if include is not None:
        sources.append(f'#include <{include}>')

    sources.append(f'void fun_023984() {{ auto x_203234234 = {expression}; }}')
    sources = '\n'.join(sources)
    tu, _ = parse_clang(sources, ext=ext, source=source)

    path = [
        CursorKind.FUNCTION_DECL,
        CursorKind.COMPOUND_STMT,
        CursorKind.DECL_STMT,
        CursorKind.VAR_DECL
    ]

    child = list(tu.cursor.get_children())[-1]
    result_type = None

    for p in path:
        assert child.kind == p, f'Expected {child.kind} == {p}'

        if child.kind == CursorKind.VAR_DECL:
            assert child.spelling == 'x_203234234'
            result_type = child.type

        children = list(child.get_children())

        if len(children) == 0:
            return None, None

        child = children[0]

    return child, result_type


if __name__ == '__main__':
    expr, type = parse_c_expression('((Sint8)0x7F)', include='SDL2/SDL.h')

    traverse(expr)
    traverse(type)




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


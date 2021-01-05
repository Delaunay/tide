from pycparser.c_parser import CParser
from pycparser.c_ast import Decl, FileAST, PtrDecl, TypeDecl, IdentifierType


_unique_name = 'unique_name'


class CType:
    def __init__(self, expr: Decl):
        self.parsed_type = expr
        self.is_const = 'const' in expr.quals
        self.is_static = 'static' in expr.storage
        self.is_pointer = isinstance(expr.type, PtrDecl)
        self.is_reference = False
        self.is_move = False

        type = expr.type
        if isinstance(type, PtrDecl) and isinstance(type.type, TypeDecl) and isinstance(type.type.type, IdentifierType):
            self.typename = type.type.type.names[0]

        if isinstance(type, TypeDecl) and isinstance(type.type, IdentifierType):
            self.typename = type.type.names[0]

    def __repr__(self):
        return f'CType(name={self.typename}, const={self.is_const}, ptr={self.is_pointer}, ref={self.is_reference})'

    @staticmethod
    def from_ast(val: FileAST) -> 'CType':
        global _unique_name

        assert len(val.ext) == 1, 'Expects a single expression'
        expr: Decl = val.ext[0]

        assert expr.name == _unique_name, 'Unexpected expression'
        return CType(expr)

    @staticmethod
    def from_string(val: str, types) -> 'CType':
        move = val.count('&&')
        no_move = val.replace('&&', '')
        ref = no_move.count('&')
        no_ref = no_move.replace('&', '')

        result = cparse_type(no_ref, types)
        result.is_move = move > 0
        result.is_reference = ref > 0
        return result


def cparse_type(text, types, filename='', debuglevel=0) -> CType:
    return cparse(f'{text} {_unique_name};', types, filename, debuglevel)


def cparse(text, types, filename='', debuglevel=0) -> CType:
    parser = CParser()

    parser.clex.filename = filename
    parser.clex.reset_lineno()
    parser._last_yielded_token = None
    parser._scope_stack = [dict()]

    for i, (k, _) in enumerate(types.items()):
        parser._add_typedef_name(k, (i, 0))

    try:
        result = parser.cparser.parse(
            input=text,
            lexer=parser.clex,
            debug=debuglevel)
    except Exception as e:
        raise RuntimeError(f'Could not parse `{text}`') from e

    return CType.from_ast(result)


if __name__ == '__main__':
    print(cparse_type('Point * const', types=dict(Point=None)))


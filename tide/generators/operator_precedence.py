import logging

from clang.cindex import Token, TokenKind

import tide.generators.nodes as T
from tide.generators.debug import show_elem, d

log = logging.getLogger(__name__)


LeftToRight = 1
RightToLeft = 2
Unary = 1
Binary = 2

operator = [
    (LeftToRight, '++', 1, 'Suffix increment',              Unary,  None),
    (LeftToRight, '--', 1, 'Suffix decrement',              Unary,  None),
    # (LeftToRight, '(' , 1, 'Function call',                 None,   None),       # (LeftToRight, ')' ): 1,
    (LeftToRight, '[' , 1, 'Array subscripting',            None,   None),  # (LeftToRight, ']' ): 1,
    (LeftToRight, '.' , 1, 'member access ',                Binary, None),
    (LeftToRight, '->', 14, 'member access through pointer', Binary, None),

    (RightToLeft, '++', 2, 'Prefix increment', Unary, '+= 1'),
    (RightToLeft, '--', 2, 'Prefix decrement', Unary, '-= 1'),
    (RightToLeft,  '+', 2, 'Unary +',          Unary, T.UAdd),
    (RightToLeft,  '-', 2, 'Unary -',          Unary, T.USub),
    (RightToLeft,  '!', 2, 'Logical NOT',      Unary, T.Not),
    (RightToLeft,  '~', 2, 'bitwise NOT',      Unary, T.Invert),
    # (RightToLeft,  '(', 2, 'Cast',             Unary, None),
    (RightToLeft,  '*', 2, 'Indirection',      Unary, None),
    (RightToLeft,  '&', 2, 'Address-of',       Unary, None),
    (RightToLeft, 'sizeof', 2, 'Size-of',      None,  None),
    (RightToLeft, '_Alignof', 2, 'Alignment requirement', None, None),

    (LeftToRight, '*', 3, 'Multiplication', Binary, T.Mult),
    (LeftToRight, '%', 3, 'Remainder', Binary, T.Mod),
    (LeftToRight, '/', 3, 'Division', Binary, T.Div),

    (LeftToRight, '+', 4, 'Add', Binary, T.Add),
    (LeftToRight, '-', 4, 'Sub', Binary, T.Sub),

    (LeftToRight, '<<', 5, 'Bitwise left shift', Binary, T.LShift),
    (LeftToRight, '>>', 5, 'Bitwise right shift', Binary, T.RShift),

    (LeftToRight, '<', 6, 'lt', Binary, T.Lt),
    (LeftToRight, '>', 6, 'gt', Binary, T.Gt),
    (LeftToRight, '<=', 6, 'lte', Binary, T.LtE),
    (LeftToRight, '>=', 6, 'gte', Binary, T.GtE),

    (LeftToRight, '==', 7, 'Equal', Binary, T.Eq),
    (LeftToRight, '!=', 7, 'Not Equal', Binary, T.NotEq),

    (LeftToRight, '&', 8, 'Bitwise AND', Binary, T.BitAnd),
    (LeftToRight, '^', 9, 'Bitwise XOR', Binary, T.BitXor),
    (LeftToRight, '|', 10, 'Bitwise OR', Binary, T.BitOr),
    (LeftToRight, '&&', 11, 'Logical AND', Binary, T.And),
    (LeftToRight, '||', 12, 'Logical OR', Binary, T.Or),

    (RightToLeft, '?', 13, 'Ternary conditional', Binary, 'if'),

    (RightToLeft, '=', 0, '', Binary, 'assign'),
    (RightToLeft, '+=', 14, '', Binary, T.UAdd),
    (RightToLeft, '-=', 14, '', Binary, T.USub),
    (RightToLeft, '*=', 14, '', Binary, T.UMult),
    (RightToLeft, '/=' , 14, '', Binary, T.UDiv),
    (RightToLeft, '%=' , 14, '', Binary, T.UMod),
    (RightToLeft, '<<=', 14, '', Binary, T.ULShift),
    (RightToLeft, '>>=', 14, '', Binary, T.URShift),
    (RightToLeft, '&=' , 14, '', Binary, T.UBitAnd),
    (RightToLeft, '^=' , 14, '', Binary, T.UBitXor),
    (RightToLeft, '|=', 14, '', Binary, T.UBitOr),

    (LeftToRight, ',', 15, 'Comma', Binary, None),
]

op_attr = {k: (a, p, n, kind, py) for (a, k, p, n, kind, py) in operator}
_none = [None, None, None, None, None]
unary_operator = {k: (a, p, n, kind, py) for (a, k, p, n, kind, py) in operator if kind is Unary}


def is_bool(op):
    return op in {'&&', '||'}


def is_comparison(op):
    return op in {'<=', '>=', '<', '>', '==', '!='}


def fetch_python_unary_op(op):
    return unary_operator.get(op, _none)[4]


def is_operator(op):
    return op in op_attr


def is_binary_operator(op):
    return op_attr.get(op, _none)[3] is Binary


def is_unary_operator(op):
    return unary_operator.get(op, _none)[3] is Unary


def fetch_precedence(op):
    return op_attr.get(op, _none)[1]


def is_right_associative(op):
    return op_attr.get(op, _none)[0]


def fetch_name(op):
    return op_attr.get(op, _none)[2]


def fetch_python_op(op):
    return op_attr.get(op, _none)[4]


class UnsupportedExpression(Exception):
    pass


class TokenParser:
    """Parse a token stream into a Python expression.
    This is used to 'parse' C macros and generate python equivalent to it
    Obviously only a small set of C is supported, for complex expression this will raise
    unsupported expression

    It is used mainly to export constant or derived constant from C to python

    Notes
    -----
    Clang cannot really help in this context as we are parsing macros and macros in C
    language are token based meaning there is no guarantee that a macro holds a valid
    expression for this reason they will never be parsed and we will have to try on our own

    Examples
    --------
    >>> from tide.generators.clang_utils  import parse_clang
    >>> from tide.generators.binding_generator  import BindingGenerator, compact, unparse
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
    def __init__(self, tokens, definitions, registry, rename):
        self.tokens = tokens
        # for tok in tokens:
        #     if tok.spelling != '\\':
        #         self.tokens.append(tok)

        if definitions is None:
            definitions = dict()

        if registry is None:
            registry = dict()

        if rename is None:
            rename = dict()

        self.pos = 0
        self.is_call = [False]
        self.definitions = definitions
        self.registry = registry
        self.rename = rename

        # there is a shit load of token kind
        # https://github.com/llvm/llvm-project/blob/master/clang/include/clang/Basic/TokenKinds.def

        self.primary_dispatch = {
            TokenKind.LITERAL: self.parse_literal,
            TokenKind.KEYWORD: self.parse_keyword,
            TokenKind.IDENTIFIER: self.parse_keyword,
        }

    def peek(self):
        if self.pos == len(self.tokens):
            return None

        return self.tokens[self.pos]

    def next(self):
        if self.pos == len(self.tokens):
            return

        self.pos += 1

    def parse_unary(self, depth):
        tok = self.peek()
        log.debug(f'{d(depth)} parse_unary {tok.kind} {tok.spelling}')

        op = tok
        self.next()
        expr = self.parse_expression(depth + 1)

        # dereference
        if op.spelling == '&':
            return expr

        if op.spelling == '*':
            return expr

        operand = fetch_python_unary_op(op.spelling)
        return T.UnaryOp(operand(), expr)

    def parse_expression(self, depth=0):
        tok = self.peek()
        log.debug(f'{d(depth)} parse_expression {tok.kind} {tok.spelling}')

        if tok.spelling == '\\\n{':
            body = []
            self.next()

            while tok.spelling != '\\\n}':
                p = T.Expr(self.parse_expression(depth + 1))
                body.append(p)

                tok = self.peek()
                if tok.spelling == ';':
                    self.next()
                    tok = self.peek()

            self.next()
            return T.If(T.Constant(True), body)

        if is_operator(tok.spelling) and is_unary_operator(tok.spelling):
            p = self.parse_unary(depth + 1)
        else:
            p = self.parse_primary(depth + 1)

        tok = self.peek()
        if tok is None:
            return p

        # we are doing a cast or call (type(expr))
        if tok.spelling == '(':
            self.next()
            expr = self.parse_call(p, depth + 1)

            if self.peek().spelling == ')':
                self.next()
            return expr

        # argument list do not try to parse operators
        if tok.spelling == ',' and self.is_call[-1]:
           return p

        if tok.spelling == ')':
            return p

        # cast (expr) <expr>
        if not is_operator(tok.spelling):
            return self.parse_cast(p, depth + 1)

        # if tok.spelling == ')':
        #    return p

        return self.parse_expression_1(p, 0, depth + 1)

    def parse_cast(self, cast_expr, depth):
        tok = self.peek()
        log.debug(f'{d(depth)} parse_cast {tok.kind} {tok.spelling}')

        expr = self.parse_expression(depth + 1)
        return T.Call(cast_expr, [expr])

    def parse_primary(self, depth):
        tok = self.peek()
        log.debug(f'{d(depth)} parse_primary {tok.kind} {tok.spelling}')

        # this can be a cast or a call
        # cast means that lhs is a type
        if tok.spelling == '(':
            self.next()
            expr = self.parse_expression(depth + 1)
            tok = self.peek()

            # lhs is a type
            if isinstance(expr, T.Name) and expr.id in self.registry:
                if tok.spelling == ')':
                    self.next()

                expr = self.parse_cast(expr, depth + 1)

            elif tok and is_operator(tok.spelling):
                return self.parse_expression_1(expr, 0, depth=depth + 1)

            elif tok and tok.spelling != ')':
                expr = self.parse_cast(expr, depth + 1)

            tok = self.peek()
            # FIXME: why is the ) already eaten
            if tok:
                assert tok.spelling == ')'
                self.next()

            return expr

        # STRINGIFY arg operation
        # this is cannot be supported
        if tok.spelling == '#':
            self.next()
            next_tok = self.peek()
            if next_tok.kind == TokenKind.IDENTIFIER:
                raise UnsupportedExpression()

        handler = self.primary_dispatch.get(tok.kind, None)

        if handler is None:
            print('----')
            show_elem(tok)
            assert False

        self.next()
        return handler(tok, depth + 1)

    unsupported_keywords = {
        '__asm__',
        # those should become decorator
        # we should try to lose as little as possible when converting between language
        '__attribute__',
        '__inline__',
        '__FILE__',
        '__func__',
        '__LINE__',
        # Macro + typedef lets pass on that
        'typedef',
        'do'
    }

    def parse_keyword(self, tok: Token, depth):
        tok_spelling = tok.spelling

        if tok.kind == TokenKind.IDENTIFIER and tok_spelling in self.rename:
            tok_spelling = self.rename[tok_spelling]

        # do the macro expansion
        elif tok.kind == TokenKind.IDENTIFIER and tok_spelling in self.definitions:
            name = tok_spelling
            v = self.definitions[name]

            # make sure we set it to a constant/expression
            while isinstance(v, T.Name):
                v = self.definitions[v.id]

            return v

        log.debug(f'{d(depth)} parse_keyword {tok.kind} {tok_spelling}')

        if tok.spelling in self.unsupported_keywords:
            raise UnsupportedExpression()

        nexttok = self.peek()

        # if
        name = tok.spelling
        if nexttok and nexttok.spelling == '*':
            self.next()
            name = f'{tok_spelling} *'

        if name in self.registry:
            name = self.registry[name]
        else:
            name = T.Name(name)

        # try to find a cast
        nexttok = self.peek()
        if nexttok and name in self.registry:
            return self.parse_cast(name, depth + 1)

        if nexttok and nexttok.spelling == '(':
            self.next()
            return self.parse_call(name, depth + 1)

        if tok.spelling in self.registry:
            return self.registry[tok_spelling]

        if isinstance(tok_spelling, str):
            return T.Name(tok_spelling)

        return tok_spelling

    def parse_call(self, expr, depth):
        log.debug(f'{d(depth)} parse_call {expr}')

        args = []

        tok = self.peek()
        self.is_call.append(True)
        while tok.spelling != ')':
            args.append(self.parse_expression(depth + 1))
            tok = self.peek()

            if tok.spelling == ',':
                self.next()
                tok = self.peek()

        self.is_call.pop()
        assert tok.spelling == ')'
        self.next()
        return T.Call(expr, args=args)

    int_types = ['ull', 'll', 'u', 'U', 'L', ]

    def parse_int(self, val):
        if val.startswith('0x'):
            return T.Constant(int(val, base=16))

        try:
            return T.Constant(int(val))
        except ValueError:
            pass

        try:
            return T.Constant(float(val))
        except ValueError:
            pass

        return None

    def is_int_annotated(self, val):
        for type in self.int_types:
            if type == val[-len(type):]:
                return len(type)
        return 0

    def parse_literal(self, tok: Token, depth):
        log.debug(f'{d(depth)} parse_literal {tok.kind} {tok.spelling}')
        val = None

        # 3243212132u
        # 0x13223u
        l = self.is_int_annotated(tok.spelling)
        if l > 0:
            val = self.parse_int(tok.spelling[:-l])

        # 1232133 | 123.123
        if val is None:
            val = self.parse_int(tok.spelling)

        # the rest
        if val is None:
            val = T.Constant(str(tok.spelling))

        return val

    def parse_expression_1(self, lhs, min_precedence, depth):
        lookahead = self.peek()
        precedence = fetch_precedence(lookahead.spelling)
        log.debug(f'{d(depth)} parse_expression_1 {lhs} {lookahead.kind} {lookahead.spelling}')

        while lookahead and precedence is not None and precedence >= min_precedence:
            op = lookahead
            self.next()

            rhs = self.parse_primary(depth + 1)
            lookahead = self.peek()

            if lookahead is None:
                break

            is_binary = is_binary_operator(lookahead.spelling)
            lookahead_pred = fetch_precedence(lookahead.spelling)
            is_right_asso = is_right_associative(lookahead.spelling)

            while lookahead and (is_binary and lookahead_pred > precedence) or (is_right_asso and lookahead_pred == precedence):
                rhs = self.parse_expression_1(rhs, lookahead_pred, depth + 1)

                lookahead = self.peek()

                is_binary = is_binary_operator(lookahead.spelling)
                lookahead_pred = fetch_precedence(lookahead.spelling)
                is_right_asso = is_right_associative(lookahead.spelling)

                if lookahead.spelling == ')':
                    break

            # the result of applying op with operands lhs and rhs
            pyop = fetch_python_op(op.spelling)

            if pyop is not None and not isinstance(pyop, str):
                if is_comparison(op.spelling):
                    lhs = T.Compare(left=lhs, ops=[pyop()], comparators=[rhs])
                elif is_bool(op.spelling):
                    lhs = T.BoolOp(op=pyop(), values=[lhs, rhs])
                else:
                    lhs = T.BinOp(left=lhs, op=pyop(), right=rhs)

            elif pyop == 'if':
                raise UnsupportedExpression()

            elif pyop == 'assign':
                lhs = T.Assign(targets=[lhs], value=rhs)

            elif op.spelling == '[':
                lhs = T.Subscript(value=lhs, slice=T.Index(value=rhs), ctx=T.Load())
                tok = self.peek()
                assert tok.spelling == ']'
                self.next()

            elif op.spelling == '->':
                if isinstance(rhs, T.Name):
                    rhs = rhs.id

                lhs = T.Attribute(lhs, rhs, ctx=T.Load())

            elif op.spelling == ',':
                lhs = T.If(T.Constant(True), [
                    T.Expr(lhs),
                    T.Return(rhs)
                ])
            else:
                show_elem(op)
                assert False

            precedence = fetch_precedence(lookahead.spelling)
        return lhs

import logging

from clang.cindex import Token, TokenKind

import tide.generators.nodes as T
from tide.generators.debug import show_elem, d


log = logging.getLogger('TIDE')

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
    (LeftToRight, '->', 1, 'member access through pointer', Binary, None),

    (RightToLeft, '++', 2, 'Prefix increment', Unary, '+= 1'),
    (RightToLeft, '--', 2, 'Prefix decrement', Unary, '-= 1'),
    (RightToLeft,  '+', 2, 'Unary +',          Unary, T.Add),
    (RightToLeft,  '-', 2, 'Unary -',          Unary, T.Sub),
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

    (RightToLeft, '=', 14, '', Binary, 'assign'),
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
    def __init__(self, tokens):
        self.tokens = tokens
        # for tok in tokens:
        #     if tok.spelling != '\\':
        #         self.tokens.append(tok)

        self.pos = 0
        self.is_call = [False]
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
        log.debug(f'{d(depth)} parse_expression {tok.kind} {tok.spelling}')

        op = tok
        self.next()
        expr = self.parse_expression(depth + 1)

        # dereference
        if op.spelling == '&':
            return expr

        operand = fetch_python_op(op.spelling)
        return T.UnaryOp(operand, expr)

    def parse_expression(self, depth=0):
        tok = self.peek()
        log.debug(f'{d(depth)} parse_expression {tok.kind} {tok.spelling}')

        if tok.spelling == '\\\n{':
            body = []
            self.next()

            while tok.spelling != '\\\n}':
                p = self.parse_expression(depth + 1)
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

        if not is_operator(tok.spelling):
            return p

        # we are doing a cast or call (type(expr))
        if tok.spelling == '(':
            self.next()
            expr = self.parse_call(p, depth + 1)
            assert self.peek().spelling == ')'
            self.next()
            return expr

        # argument list do not try to parse operators
        if tok.spelling == ',' and self.is_call[-1]:
           return p

        # if tok.spelling == ')':
        #    return p

        return self.parse_expression_1(p, 0, depth + 1)

    def parse_cast(self, cast_expr, depth):
        expr = self.parse_expression(depth + 1)
        return T.Call(cast_expr, [expr])

    def parse_primary(self, depth):
        tok = self.peek()
        log.debug(f'{d(depth)} parse_primary {tok.kind} {tok.spelling}')

        if tok.spelling == '(':
            self.next()
            expr = self.parse_expression(depth + 1)
            tok = self.peek()

            # we are doing a cast
            # (()  expr)
            if tok and tok.spelling != ')':
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

    def parse_keyword(self, tok: Token, depth):
        log.debug(f'{d(depth)} parse_keyword {tok.kind} {tok.spelling}')

        nexttok = self.peek()
        if nexttok and nexttok.spelling == '(':
            self.next()
            return self.parse_call(T.Name(tok.spelling), depth + 1)

        if nexttok and nexttok.spelling == '*':
            # FIXME: we ignore `*`
            # void*
            self.next()

        if tok.spelling == '__asm__':
            raise UnsupportedExpression()

        return T.Name(tok.spelling)

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

    def parse_literal(self, tok: Token, depth):
        log.debug(f'{d(depth)} parse_literal {tok.kind} {tok.spelling}')

        if '0x' in tok.spelling:
            val = tok.spelling

            val = val.replace('u', '')
            val = val.replace('ll', '')
            val = val.replace('U', '')
            val = val.replace('L', '')

            return T.Constant(int(val, base=16))

        try:
            value_i = int(tok.spelling)
            value_f = float(tok.spelling)

            if value_f == value_i:
                return T.Constant(value_i)

            return T.Constant(value_f)
        except ValueError:
            return T.Constant(str(tok.spelling))

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
                print(pyop)
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
                lhs = T.Attribute(lhs, rhs, ctx=T.Load())

            elif op.spelling == ',':
                lhs = T.If(T.Constant(True), [
                    lhs,
                    rhs
                ])
            else:
                show_elem(op)
                assert False

            precedence = fetch_precedence(lookahead.spelling)
        return lhs

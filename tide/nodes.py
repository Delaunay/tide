from dataclasses import dataclass
from typing import *


Identifier = str


class Node:
    pass


class Statement(Node):
    pass


class Expression(Node):
    pass


class Operator(Node):
    pass


class Slice(Node):
    pass


class ExpressionContext(Node):
    pass


#  comprehension Product([Field(expr, target), Field(expr, iter), Field(expr, ifs, seq=True), Field(int, is_async)])
@dataclass
class Comprehension:
    target: Expression
    iter: Expression
    ifs: List[Expression]
    is_async: int


#  excepthandler Constructor(ExceptHandler, [Field(expr, type, opt=True), Field(identifier, name, opt=True), Field(stmt, body, seq=True)])
@dataclass
class ExceptHandler:
    type: Optional[Expression]
    name: Optional[Identifier]
    body: List[Statement]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  arg Product([Field(identifier, arg), Field(expr, annotation, opt=True), Field(string, type_comment, opt=True)], [Field(int, lineno), Field(int, col_offset), Field(int, end_lineno, opt=True), Field(int, end_col_offset, opt=True)])
@dataclass
class Arg:
    arg: Identifier
    annotation: Optional[Expression]
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  arguments Product([Field(arg, posonlyargs, seq=True), Field(arg, args, seq=True), Field(arg, vararg, opt=True), Field(arg, kwonlyargs, seq=True), Field(expr, kw_defaults, seq=True), Field(arg, kwarg, opt=True), Field(expr, defaults, seq=True)])
@dataclass
class Arguments:
    posonlyargs: List[Arg]
    args: List[Arg]
    vararg: Optional[Arg]
    kwonlyargs: List[Arg]
    kw_defaults: List[Expression]
    kwarg: Optional[Arg]
    defaults: List[Expression]

#  keyword Product([Field(identifier, arg, opt=True), Field(expr, value)])
@dataclass
class Keyword:
    arg: Optional[Identifier]
    value: Expression


#  alias Product([Field(identifier, name), Field(identifier, asname, opt=True)])
@dataclass
class Alias:
    name: Identifier
    asname: Optional[Identifier]


#  withitem Product([Field(expr, context_expr), Field(expr, optional_vars, opt=True)])
@dataclass
class Withitem:
    context_expr: Expression
    optional_vars: Optional[Expression]


#  type_ignore Constructor(TypeIgnore, [Field(int, lineno), Field(string, tag)])
@dataclass
class TypeIgnore:
    lineno: int
    tag: str


#  mod Constructor(Module, [Field(stmt, body, seq=True), Field(type_ignore, type_ignores, seq=True)])
@dataclass
class Module(Node):
    body: List[Statement]
    type_ignores = None


#  mod Constructor(Interactive, [Field(stmt, body, seq=True)])
@dataclass
class Interactive(Module):
    body: List[Statement]


#  mod Constructor(Expression, [Field(expr, body)])
@dataclass
class Expression(Module):
    body: Expression


#  mod Constructor(FunctionType, [Field(expr, argtypes, seq=True), Field(expr, returns)])
@dataclass
class FunctionType(Module):
    argtypes: List[Expression]
    returns: Expression


#  mod Constructor(Suite, [Field(stmt, body, seq=True)])
@dataclass
class Suite(Module):
    body: List[Statement]


#  stmt Constructor(FunctionDef, [Field(identifier, name), Field(arguments, args), Field(stmt, body, seq=True), Field(expr, decorator_list, seq=True), Field(expr, returns, opt=True), Field(string, type_comment, opt=True)])
@dataclass
class FunctionDef(Statement):
    name: Identifier
    args: Arguments
    body: List[Statement]
    decorator_list: List[Expression]
    returns: Optional[Expression]
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(AsyncFunctionDef, [Field(identifier, name), Field(arguments, args), Field(stmt, body, seq=True), Field(expr, decorator_list, seq=True), Field(expr, returns, opt=True), Field(string, type_comment, opt=True)])
@dataclass
class AsyncFunctionDef(Statement):
    name: Identifier
    args: Arguments
    body: List[Statement]
    decorator_list: List[Expression]
    returns: Optional[Expression]
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(ClassDef, [Field(identifier, name), Field(expr, bases, seq=True), Field(keyword, keywords, seq=True), Field(stmt, body, seq=True), Field(expr, decorator_list, seq=True)])
@dataclass
class ClassDef(Statement):
    name: Identifier
    bases: List[Expression]
    keywords: List[Keyword]
    body: List[Statement]
    decorator_list: List[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Return, [Field(expr, value, opt=True)])
@dataclass
class Return(Statement):
    value: Optional[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Delete, [Field(expr, targets, seq=True)])
@dataclass
class Delete(Statement):
    targets: List[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Assign, [Field(expr, targets, seq=True), Field(expr, value), Field(string, type_comment, opt=True)])
@dataclass
class Assign(Statement):
    targets: List[Expression]
    value: Expression
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(AugAssign, [Field(expr, target), Field(operator, op), Field(expr, value)])
@dataclass
class AugAssign(Statement):
    target: Expression
    op: Operator
    value: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(AnnAssign, [Field(expr, target), Field(expr, annotation), Field(expr, value, opt=True), Field(int, simple)])
@dataclass
class AnnAssign(Statement):
    target: Expression
    annotation: Expression
    value: Optional[Expression]
    simple: int
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(For, [Field(expr, target), Field(expr, iter), Field(stmt, body, seq=True), Field(stmt, orelse, seq=True), Field(string, type_comment, opt=True)])
@dataclass
class For(Statement):
    target: Expression
    iter: Expression
    body: List[Statement]
    orelse: List[Statement]
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(AsyncFor, [Field(expr, target), Field(expr, iter), Field(stmt, body, seq=True), Field(stmt, orelse, seq=True), Field(string, type_comment, opt=True)])
@dataclass
class AsyncFor(Statement):
    target: Expression
    iter: Expression
    body: List[Statement]
    orelse: List[Statement]
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(While, [Field(expr, test), Field(stmt, body, seq=True), Field(stmt, orelse, seq=True)])
@dataclass
class While(Statement):
    test: Expression
    body: List[Statement]
    orelse: List[Statement]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(If, [Field(expr, test), Field(stmt, body, seq=True), Field(stmt, orelse, seq=True)])
@dataclass
class If(Statement):
    test: Expression
    body: List[Statement]
    orelse: List[Statement]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(With, [Field(withitem, items, seq=True), Field(stmt, body, seq=True), Field(string, type_comment, opt=True)])
@dataclass
class With(Statement):
    items: List[Withitem]
    body: List[Statement]
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(AsyncWith, [Field(withitem, items, seq=True), Field(stmt, body, seq=True), Field(string, type_comment, opt=True)])
@dataclass
class AsyncWith(Statement):
    items: List[Withitem]
    body: List[Statement]
    type_comment: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Raise, [Field(expr, exc, opt=True), Field(expr, cause, opt=True)])
@dataclass
class Raise(Statement):
    exc: Optional[Expression]
    cause: Optional[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Try, [Field(stmt, body, seq=True), Field(excepthandler, handlers, seq=True), Field(stmt, orelse, seq=True), Field(stmt, finalbody, seq=True)])
@dataclass
class Try(Statement):
    body: List[Statement]
    handlers = None
    orelse: List[Statement]
    finalbody: List[Statement]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Assert, [Field(expr, test), Field(expr, msg, opt=True)])
@dataclass
class Assert(Statement):
    test: Expression
    msg: Optional[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Import, [Field(alias, names, seq=True)])
@dataclass
class Import(Statement):
    names: List[Alias]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(ImportFrom, [Field(identifier, module, opt=True), Field(alias, names, seq=True), Field(int, level, opt=True)])
@dataclass
class ImportFrom(Statement):
    module: Optional[Identifier]
    names: List[Alias]
    level: Optional[int]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Global, [Field(identifier, names, seq=True)])
@dataclass
class Global(Statement):
    names: List[Identifier]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Nonlocal, [Field(identifier, names, seq=True)])
@dataclass
class Nonlocal(Statement):
    names: List[Identifier]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Expr, [Field(expr, value)])
@dataclass
class Expr(Statement):
    value: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Pass, [])
@dataclass
class Pass(Statement):
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Break, [])
@dataclass
class Break(Statement):
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  stmt Constructor(Continue, [])
@dataclass
class Continue(Statement):
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(BoolOp, [Field(boolop, op), Field(expr, values, seq=True)])
@dataclass
class BoolOp(Expression):
    op: 'BoolOp'
    values: List[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(NamedExpr, [Field(expr, target), Field(expr, value)])
@dataclass
class NamedExpr(Expression):
    target: Expression
    value: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(BinOp, [Field(expr, left), Field(operator, op), Field(expr, right)])
@dataclass
class BinOp(Expression):
    left: Expression
    op: 'BinOp'
    right: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(UnaryOp, [Field(unaryop, op), Field(expr, operand)])
@dataclass
class UnaryOp(Expression):
    op: 'UnaryOp'
    operand: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Lambda, [Field(arguments, args), Field(expr, body)])
@dataclass
class Lambda(Expression):
    args: Arguments
    body: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(IfExp, [Field(expr, test), Field(expr, body), Field(expr, orelse)])
@dataclass
class IfExp(Expression):
    test: Expression
    body: Expression
    orelse: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Dict, [Field(expr, keys, seq=True), Field(expr, values, seq=True)])
@dataclass
class Dict(Expression):
    keys: List[Expression]
    values: List[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Set, [Field(expr, elts, seq=True)])
@dataclass
class Set(Expression):
    elts: List[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(ListComp, [Field(expr, elt), Field(comprehension, generators, seq=True)])
@dataclass
class ListComp(Expression):
    elt: Expression
    generators: List[Comprehension]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(SetComp, [Field(expr, elt), Field(comprehension, generators, seq=True)])
@dataclass
class SetComp(Expression):
    elt: Expression
    generators: List[Comprehension]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(DictComp, [Field(expr, key), Field(expr, value), Field(comprehension, generators, seq=True)])
@dataclass
class DictComp(Expression):
    key: Expression
    value: Expression
    generators: List[Comprehension]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(GeneratorExp, [Field(expr, elt), Field(comprehension, generators, seq=True)])
@dataclass
class GeneratorExp(Expression):
    elt: Expression
    generators: List[Comprehension]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Await, [Field(expr, value)])
@dataclass
class Await(Expression):
    value: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Yield, [Field(expr, value, opt=True)])
@dataclass
class Yield(Expression):
    value: Optional[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(YieldFrom, [Field(expr, value)])
@dataclass
class YieldFrom(Expression):
    value: Expression
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Compare, [Field(expr, left), Field(cmpop, ops, seq=True), Field(expr, comparators, seq=True)])
@dataclass
class Compare(Expression):
    left: Expression
    ops: 'Compare'
    comparators: List[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Call, [Field(expr, func), Field(expr, args, seq=True), Field(keyword, keywords, seq=True)])
@dataclass
class Call(Expression):
    func: Expression
    args: List[Expression]
    keywords: List[Keyword]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(FormattedValue, [Field(expr, value), Field(int, conversion, opt=True), Field(expr, format_spec, opt=True)])
@dataclass
class FormattedValue(Expression):
    value: Expression
    conversion: Optional[int]
    format_spec: Optional[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(JoinedStr, [Field(expr, values, seq=True)])
@dataclass
class JoinedStr(Expression):
    values: List[Expression]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Constant, [Field(constant, value), Field(string, kind, opt=True)])
@dataclass
class Constant(Expression):
    value = None
    kind: Optional[str]
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Attribute, [Field(expr, value), Field(identifier, attr), Field(expr_context, ctx)])
@dataclass
class Attribute(Expression):
    value: Expression
    attr: Identifier
    ctx: ExpressionContext
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Subscript, [Field(expr, value), Field(slice, slice), Field(expr_context, ctx)])
@dataclass
class Subscript(Expression):
    value: Expression
    slice: Slice
    ctx: ExpressionContext
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Starred, [Field(expr, value), Field(expr_context, ctx)])
@dataclass
class Starred(Expression):
    value: Expression
    ctx: ExpressionContext
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Name, [Field(identifier, id), Field(expr_context, ctx)])
@dataclass
class Name(Expression):
    id: Identifier
    ctx: ExpressionContext
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(List, [Field(expr, elts, seq=True), Field(expr_context, ctx)])
@dataclass
class ListN(Expression):
    elts: List[Expression]
    ctx: ExpressionContext
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr Constructor(Tuple, [Field(expr, elts, seq=True), Field(expr_context, ctx)])
@dataclass
class TupleN(Expression):
    elts: List[Expression]
    ctx: ExpressionContext
    lineno: int
    col_offset: int
    end_lineno: Optional[int]
    end_col_offset: Optional[int]


#  expr_context Constructor(Load, [])
@dataclass
class Load(ExpressionContext):
    pass


#  expr_context Constructor(Store, [])
@dataclass
class Store(ExpressionContext):
    pass


#  expr_context Constructor(Del, [])
@dataclass
class Del(ExpressionContext):
    pass


#  expr_context Constructor(AugLoad, [])
@dataclass
class AugLoad(ExpressionContext):
    pass


#  expr_context Constructor(AugStore, [])
@dataclass
class AugStore(ExpressionContext):
    pass


#  expr_context Constructor(Param, [])
@dataclass
class Param(ExpressionContext):
    pass


#  slice Constructor(Slice, [Field(expr, lower, opt=True), Field(expr, upper, opt=True), Field(expr, step, opt=True)])
@dataclass
class Slice(Slice):
    lower: Optional[Expression]
    upper: Optional[Expression]
    step: Optional[Expression]


#  slice Constructor(ExtSlice, [Field(slice, dims, seq=True)])
@dataclass
class ExtSlice(Slice):
    dims: List[Slice]


#  slice Constructor(Index, [Field(expr, value)])
@dataclass
class Index(Slice):
    value: Expression


#  boolop Constructor(And, [])
@dataclass
class And(BoolOp):
    pass


#  boolop Constructor(Or, [])
@dataclass
class Or(BoolOp):
    pass


#  operator Constructor(Add, [])
@dataclass
class Add(Operator):
    pass


#  operator Constructor(Sub, [])
@dataclass
class Sub(Operator):
    pass


#  operator Constructor(Mult, [])
@dataclass
class Mult(Operator):
    pass


#  operator Constructor(MatMult, [])
@dataclass
class MatMult(Operator):
    pass


#  operator Constructor(Div, [])
@dataclass
class Div(Operator):
    pass


#  operator Constructor(Mod, [])
@dataclass
class Mod(Operator):
    pass


#  operator Constructor(Pow, [])
@dataclass
class Pow(Operator):
    pass


#  operator Constructor(LShift, [])
@dataclass
class LShift(Operator):
    pass


#  operator Constructor(RShift, [])
@dataclass
class RShift(Operator):
    pass


#  operator Constructor(BitOr, [])
@dataclass
class BitOr(Operator):
    pass


#  operator Constructor(BitXor, [])
@dataclass
class BitXor(Operator):
    pass


#  operator Constructor(BitAnd, [])
@dataclass
class BitAnd(Operator):
    pass


#  operator Constructor(FloorDiv, [])
@dataclass
class FloorDiv(Operator):
    pass


#  unaryop Constructor(Invert, [])
@dataclass
class Invert(UnaryOp):
    pass


#  unaryop Constructor(Not, [])
@dataclass
class Not(UnaryOp):
    pass


#  unaryop Constructor(UAdd, [])
@dataclass
class UAdd(UnaryOp):
    pass


#  unaryop Constructor(USub, [])
@dataclass
class USub(UnaryOp):
    pass


#  cmpop Constructor(Eq, [])
@dataclass
class Eq(Compare):
    pass


#  cmpop Constructor(NotEq, [])
@dataclass
class NotEq(Compare):
    pass


#  cmpop Constructor(Lt, [])
@dataclass
class Lt(Compare):
    pass


#  cmpop Constructor(LtE, [])
@dataclass
class LtE(Compare):
    pass


#  cmpop Constructor(Gt, [])
@dataclass
class Gt(Compare):
    pass


#  cmpop Constructor(GtE, [])
@dataclass
class GtE(Compare):
    pass


#  cmpop Constructor(Is, [])
@dataclass
class Is(Compare):
    pass


#  cmpop Constructor(IsNot, [])
@dataclass
class IsNot(Compare):
    pass


#  cmpop Constructor(In, [])
@dataclass
class In(Compare):
    pass


#  cmpop Constructor(NotIn, [])
@dataclass
class NotIn(Compare):
    pass

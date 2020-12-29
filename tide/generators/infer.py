import ast as pyast
from typing import *

import tide.generators.nodes as ast
from tide.generators.utils import ProjectFolder
from tide.generators.utils import reserved, builtintypes

class KiwiType:
    pass

class MetaType:
    def __init__(self):
        self.clues= []

    def add_clue(self, clue):
        self.clues.append(clue)


class NoneType(KiwiType):
    pass


class TypeType(KiwiType):
    pass


class StructType(KiwiType):
    def __init__(self, types):
        self.types = types


class UnionType(KiwiType):
    def __init__(self, types):
        self.types = types


def get_type(code, name=None):
    import ast
    module = ast.parse(code)
    inferrer = TypeInference(ProjectFolder('.'), '')

    expr_type = None
    for b in module.body:
        _, expr_type = inferrer.exec(b)

    if name is None:
        return expr_type

    return inferrer.typing_context.get(name)


class TypingContext:
    def __init__(self, visitor, parent=None, depth=0):
        self.name = 'root'
        self.visitor = visitor
        self.parent = parent
        self.depth = depth
        self.scope = dict()

    def __setitem__(self, key, value):
        self.scope[key] = value

    def __enter__(self):
        new_context = TypingContext(self.visitor, self, self.depth + 1)
        self.visitor.typing_context = new_context
        return new_context

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.visitor.typing_context = self

    def __getitem__(self, item):
        if self.parent is None or item in self.scope:
            return self.scope[item]
        return self.parent[item]

    def get(self, item, default=None):
        if self.parent is None or item in self.scope:
            return self.scope.get(item, default)
        return self.parent.get(item, default)


class TypeInference:
    def __init__(self, project: ProjectFolder, filename):
        self.project = project
        self.filename = filename
        self.typing_context = TypingContext(self)
        self.class_scope = None

    @staticmethod
    def _getname(obj):
        name = type(obj).__name__.lower()
        if name in reserved:
            name = '_' + name
        return name

    def tuple(self, obj: ast.Tuple, **kwargs):
        """
        Examples
        --------
        >>> import ast
        >>> get_type("(0, 1, 2.0, '123')")
        typing.Tuple[int, int, float, str]
        """
        types = []
        for e in obj.elts:
            value, type = self.exec(e, **kwargs)
            types.append(type)

        type = Tuple[()]
        type.__args__ = tuple(types)
        return obj, type

    def _raise(self, obj: ast.Raise, depth, **kwargs):
        return obj, None

    def num(self, obj: ast.Num, **kwargs):
        return obj, type(obj.n)

    def str(self, obj: ast.Str, **kwargs):
        return obj, str

    def nameconstant(self, obj: ast.NameConstant, **kwargs):
        return obj, type(obj)

    def infer_container(self, obj, **kwargs):
        types = []
        for e in obj.elts:
            _, element_type = self.exec(e, **kwargs)
            types.append(element_type)

        first = types[0]
        for element_type in types:
            if isinstance(element_type, first):
                print(f'warning type mismatch {element_type} != {first}')

        return obj, first

    def set(self, obj: ast.Set, **kwargs):
        """
        Examples
        --------
        >>> import ast
        >>> get_type(
        ... "{0, 1}"
        ... )
        typing.Set[int]
        """
        _, t = self.infer_container(obj, **kwargs)
        return obj, Set[t]

    def list(self, obj: ast.List, **kwargs):
        """
        Examples
        --------
        >>> import ast
        >>> get_type(
        ... "[0, 1]"
        ... )
        typing.List[int]
        """
        _, t = self.infer_container(obj, **kwargs)
        return obj, List[t]

    def dict(self, obj: ast.Dict, **kwargs):
        """
        Examples
        --------
        >>> import ast
        >>> get_type(
        ... "{'a': 1, 'b': 2}"
        ... )
        typing.Dict[str, int]
        """
        types = []
        for k, v in zip(obj.keys, obj.values):
            _, key_type = self.exec(k, **kwargs)
            _, value_type = self.exec(v, **kwargs)
            types.append((key_type, value_type))

        first = types[0]
        for kt, vt in types:
            if isinstance(kt, first[0]):
                print(f'warning type mismatch {kt} != {first[0]}')

            if isinstance(vt, first[1]):
                print(f'warning type mismatch {vt} != {first[0]}')

        return obj, Dict[first[0], first[1]]

    def augassign(self, obj: ast.AugAssign, **kwargs):
        # might not need to infer this because an assign needed to be there before
        # value, _ = self.exec(obj.value, **kwargs)
        _, type = self.exec(obj.target, **kwargs)
        return obj, type

    def _if(self, obj: ast.If, **kwargs):
        return obj, None

    def unaryop(self, obj: ast.UnaryOp, **kwargs):
        _, type = self.exec(obj.operand, **kwargs)
        return obj, type

    def expr(self, obj: ast.Expr, **kwargs):
        _, t = self.exec(obj.value, **kwargs)
        return obj, t

    def compare(self, obj: ast.Compare, **kwargs):
        _, lhs_type = self.exec(obj.left, **kwargs)

        for b in obj.comparators:
            _, rhs_type = self.exec(b, **kwargs)

        # operator...
        return obj, bool

    def run(self, module):
        self.exec(module, depth=0)

    def boolop(self, obj: ast.BoolOp, **kwargs):
        return obj, bool

    def subscript(self, obj: ast.Subscript, **kwargs):
        _, type = self.exec(obj.value, **kwargs)
        return obj, type

    def importfrom(self, obj: ast.ImportFrom, **kwargs):
        return obj, None

    def exec(self, obj, **kwargs):
        try:
            fun = getattr(self, self._getname(obj))
            return fun(obj, **kwargs)
        except Exception as e:
            print(f'Error when processing {obj}')
            raise e

    def _while(self, obj: ast.While, **kwargs):
        for b in obj.body:
            self.exec(b, **kwargs)
        return obj, None

    def _pass(self, obj: ast.Pass, **kwargs):
        return obj, None

    def call(self, obj: ast.Call, **kwargs):
        """
        Examples
        --------
        >>> import ast
        >>> get_type(
        ...     "def add(a: int, b: int) -> int:\\n"
        ...     "   return a + b\\n"
        ...     "\\n"
        ...     "a = add(1, 2)\\n",
        ...     name='a'
        ... )
        <class 'int'>
        """
        fun, callable_type = self.exec(obj.func, **kwargs)
        arg_types = callable_type.__args__[:-1]
        return_type = callable_type.__args__[-1]

        args = []
        for arg, expected_type in zip(obj.args, arg_types):
            _, arg_type = self.exec(arg, expected_type=expected_type, **kwargs)
            args.append(arg_type)

            if not self.typecheck(arg_type, expected_type):
                print('mistyping')

        # Python nor C++ supports partial call natively
        return obj, return_type

    def module(self, obj: ast.Module, **kwargs):
        for expr in obj.body:
            expr, type = self.exec(expr, **kwargs)

    def assign_global(self, expr: ast.Assign):
        type = self.exec(expr.value)
        return expr, type

    def typecheck(self, a, expected_type):
        return True

    def annassign_global(self, expr: ast.AnnAssign):
        value, inferred_type = self.exec(expr.value)
        type_constraint = self.exec_type(expr.annotation)

        if not self.typecheck(inferred_type, type_constraint):
            print('Typing error')

        # Type annotation is user defined and take precedence on the inferred type
        # the reason why is that user can add type annotation to pin point exactly where
        # the mistyping is
        return expr, type_constraint

    def name(self, obj: ast.Name, expected_type=None, **kwargs):
        type = self.typing_context.get(obj.id, None)

        if type is None and expected_type is not None:
            type = expected_type
            self.typing_context[obj.id] = expected_type

        if obj.id in builtintypes:
            return builtintypes[obj.id], TypeType

        if type is None and expected_type is None:
            print(f'Untyped variable {obj.id}')

        return obj, type

    def binop(self, obj: ast.BinOp, **kwargs):
        lhs, lhs_type = self.exec(obj.left, **kwargs)
        # TODO: check if the operator is supported by that type
        # This is wrong we can expect rhs & lhs to be of a different types
        # we should fetch the function that match and return its return_type
        # similar to what is done in ast.Call
        rhs, rhs_type = self.exec(obj.right, **kwargs)

        if not self.typecheck(rhs_type, expected_type=lhs_type):
            print('')

        return obj, rhs_type

    def _return(self, obj: ast.Return, **kwargs):
        _, type = self.exec(obj.value, **kwargs)
        return obj, type

    def _import(self, obj: ast.Import, **kwargs):
        # This should fetch the imported element so we can type check its usage
        return obj, None

    def attribute(self, obj: ast.Attribute, expected_type=None, **kwargs):
        attr_type = self.typing_context.get(obj.attr)

        if expected_type and attr_type:
            # attr_type here is the expected type
            # expected_type is coming from the assign expression
            self.typecheck(expected_type, attr_type)

        if expected_type is None:
            expected_type = attr_type

        if expected_type is None:
            print(f'Missing attribute type {obj}')

        if self.class_scope:
            self.class_scope[obj.attr] = expected_type
            return obj, expected_type

        return obj, expected_type

    def assign(self, obj: ast.Assign, **kwargs):
        _, target_type = self.exec(obj.value, **kwargs)

        target_types = [target_type]
        if hasattr(target_type, '__args__'):
            target_types = target_type.__args__

        for target, expected_type in zip(obj.targets, target_types):
            self.exec(target, expected_type=expected_type, **kwargs)

        return None, NoneType

    def annassign(self, obj: ast.AnnAssign, **kwargs):
        expected_type = self.exec_type(obj.annotation, **kwargs)
        expr, expr_type = self.exec(obj.value, **kwargs)

        if not self.typecheck(expr_type, expected_type):
            print(f'Type mismatch {expected_type} != {expr_type}')

        return obj, expected_type

    def exec_type(self, expr, **kwargs):
        return self.exec(expr, **kwargs)

    def functiondef(self, obj: ast.FunctionDef, **kwargs):
        """
        Examples
        --------
        >>> import ast
        >>> get_type(
        ... "def add(a: int, b: int) -> int:\\n"
        ... "   return a + b\\n"
        ... )
        typing.Callable[[int, int], int]
        """
        return_type, typetype = self.exec_type(obj.returns, **kwargs)

        with self.typing_context as scope:
            scope.name = obj.name

            offset = 0
            args = []

            for arg in obj.args.args[offset:]:
                arg_type = MetaType()
                if arg.annotation is not None:
                    arg_type, typetype = self.exec_type(arg.annotation, **kwargs)

                scope[arg.arg] = arg_type
                args.append(arg_type)

            _, type = self.function_body(obj, **kwargs)

        fun_type = Callable[args, return_type]
        self.typing_context[obj.name] = fun_type
        return obj, fun_type

    def function_body(self, obj: ast.FunctionDef, **kwargs):
        body = []
        for b in obj.body:
            self.exec(b, **kwargs)

        return obj.body, None

    def nonetype(self, obj, **kwargs):
        return None, NoneType

    def classdef(self, obj: ast.ClassDef, **kwargs):
        """To match Python object behaviour all classes are instantiated as shared pointer"""
        with self.typing_context as scope:
             = scope
            scope.name = obj.name
            scope['self'] = obj

        return obj, obj


if __name__ == '__main__':
    pass

import ast as pyast

import tide.generators.nodes as ast
from tide.generators.utils import ProjectFolder
from tide.generators.utils import reserved, builtintypes, typing_types, operator_magic

from tide.generators.cpp.retypes import *
from tide.generators.cpp.parse_type import CType


def get_type(code, name=None):
    import ast
    module = ast.parse(code)
    inferer = TypeInference(ProjectFolder('.'), '')

    expr_type = None
    for b in module.body:
        expr, expr_type = inferer.exec(b)

        if expr_type is TypeType:
            expr_type = expr

    if name is None:
        return expr_type

    return inferer.typing_context.get(name)


class TypingContext:
    def __init__(self, visitor, parent=None, depth=0):
        self.name = 'root'
        self.visitor = visitor
        self.parent = parent
        self.depth = depth
        self.scope = dict()

    def __iter__(self):
        return self

    def items(self):
        for r in self.scope.items():
            yield r

        if self.parent is not None:
            for r in self.parent.items():
                yield r

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
        self.class_scopes = []
        self.function_scopes = []
        # Hold the typing information for all expressions inside a module
        self.scopes = dict(root=self.typing_context)
        self.init_capture = False

    def class_name(self):
        if self.class_scopes:
            return self.class_scopes[-1].name
        return ''

    def function_name(self):
        if self.function_scopes:
            return self.function_scopes[-1].name
        return ''

    def diagnostic(self, obj, *args, **kwargs):
        diagnostic = ''
        if hasattr(obj, 'lineno'):
            diagnostic = f':L{obj.lineno} C{obj.col_offset}'

        class_name = self.class_name()
        function = self.function_name()

        entity = ''
        if class_name or function:
            entity = f' {class_name}::{function}'

        print(f'[INFER] {self.project.project_name}/{self.filename}{diagnostic}{entity} -', *args, **kwargs)

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

        return obj, Generic('Tuple', *types)

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
        element_type = None
        for e in obj.elts:
            _, element_type = self.exec(e, expected_type=element_type, **kwargs)
            types.append(element_type)

        first = MetaType()
        if len(types) > 0 and not isinstance(types[0], MetaType):
            first = types[0]

            for element_type in types:
                if isinstance(element_type, first):
                    self.diagnostic(obj, f'type mismatch {element_type} != {first}')
        else:
            self.diagnostic(obj, 'was not able to infer type')

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
        return obj, Generic('Set', t)

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
        return obj, Generic('List', t)

    def dict(self, obj: ast.Dict, expected_type=None, **kwargs):
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
        key_type = None
        value_type = None
        for k, v in zip(obj.keys, obj.values):
            _, key_type = self.exec(k, expected_type=key_type, **kwargs)
            _, value_type = self.exec(v, expected_type=value_type, **kwargs)
            types.append((key_type, value_type))

        first = [None, None]

        for kt, vt in types:
            if not isinstance(kt, MetaType):
                first[0] = kt

            if not isinstance(vt, MetaType):
                first[1] = vt

        if first[0] is None and first[1] is None:
            if expected_type is None:
                return obj, Generic('Dict', MetaType(), MetaType())
            else:
                # TODO check that expected_type is a Dict at the very least
                return obj, expected_type

        for kt, vt in types:
            if isinstance(kt, first[0]):
                self.diagnostic(obj, f'type mismatch {kt} != {first[0]}')

            if isinstance(vt, first[1]):
                self.diagnostic(obj, f'type mismatch {vt} != {first[0]}')

        dict_type = Generic('Dict', first[0], first[1])
        if expected_type is not None and not self.typecheck(obj, dict_type, expected_type):
            pass

        return obj, dict_type

    def augassign(self, obj: ast.AugAssign, **kwargs):
        # the variable we are setting should be already defined
        _, target_type = self.exec(obj.target, **kwargs)
        _, value_type = self.exec(obj.value, expected_type=target_type, **kwargs)

        if not self.typecheck(obj, value_type, target_type):
            pass

        # target_type takes precedence here because that type comes
        # from the variable definition
        return obj, target_type

    def _if(self, obj: ast.If, **kwargs):
        self.exec(obj.test)

        for b in obj.body:
            self.exec(b, **kwargs)

        for b in obj.orelse:
            self.exec(b, **kwargs)

        return obj, None

    def unaryop(self, obj: ast.UnaryOp, **kwargs):
        _, type = self.exec(obj.operand, **kwargs)
        # TODO check that the unary op is supported by that type
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
        return self.scopes

    def boolop(self, obj: ast.BoolOp, **kwargs):
        for b in obj.values:
            self.exec(b, **kwargs)

        return obj, bool

    def subscript(self, obj: ast.Subscript, **kwargs):
        """
        Examples
        --------
        Guess variable's typing from a function call
        >>> import ast
        >>> get_type(
        ...     "a = [1, 2, 3]\\n"
        ...     "b = a[1]\\n",
        ...     name='b'
        ... )
        <class 'int'>

        Process a type
        >>> import ast
        >>> type_expr = get_type("Tuple[int, float]").value
        >>> type_expr.value.id
        'Tuple'
        >>> [e.id for e in type_expr.slice.value.elts]
        ['int', 'float']
        """

        if isinstance(obj.value, pyast.Name) and obj.value.id in typing_types:
            return obj, TypeType

        # <value>[<slice>]
        _, object_type = self.exec(obj.value, **kwargs)
        element_type = object_type

        # TODO: hack for now
        if isinstance(object_type, Generic) and isinstance(obj.slice, pyast.Index):
            element_type = object_type.types[0]

        return obj, element_type

    def importfrom(self, obj: ast.ImportFrom, **kwargs):
        for alias in obj.names:
            name = alias.name
            if alias.asname is not None:
                name = alias.asname

            # TODO: get the type of the imported entity
            self.typing_context[name] = None

        return obj, None

    def exec(self, obj, **kwargs):
        try:
            fun = getattr(self, self._getname(obj))
            return fun(obj, **kwargs)
        except Exception as e:

            self.diagnostic(obj, f'Error when processing {self.class_name()}::{self.function_name()} in {obj}')
            raise e

    def _while(self, obj: ast.While, **kwargs):
        self.exec(obj.test)

        for b in obj.body:
            self.exec(b, **kwargs)

        for b in obj.orelse:
            self.exec(b, **kwargs)

        return obj, None

    def _pass(self, obj: ast.Pass, **kwargs):
        return obj, None

    def call(self, obj: ast.Call, expected_type=None, **kwargs):
        """
        Examples
        --------
        Guess variable's typing from a function call
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
        expected_return_type = expected_type
        fun, callable_type = self.exec(obj.func, **kwargs)

        if isinstance(callable_type, Callable):
            arg_types = callable_type.args
            return_type = callable_type.return_type

        elif isinstance(callable_type, pyast.ClassDef):
            scope = self.scopes[callable_type]
            ctor_type = scope.get('__init__')

            if isinstance(ctor_type, Callable):
                arg_types = ctor_type.args
                return_type = ctor_type.return_type
            else:
                self.diagnostic(obj, f'Unable to process object constructor {callable_type} => {ctor_type}')
                arg_types = [MetaType() for _ in obj.args]
                return_type = MetaType()

        else:
            self.diagnostic(obj, f'Function call type not found for {pyast.dump(obj.func)} type={callable_type}')
            arg_types = [MetaType() for _ in obj.args]
            return_type = MetaType()

        args = []
        for arg, expected_type in zip(obj.args, arg_types):
            _, arg_type = self.exec(arg, expected_type=expected_type, **kwargs)
            args.append(arg_type)

            if not self.typecheck(obj, arg_type, expected_type):
                pass

        if not self.typecheck(obj, return_type, expected_return_type):
            pass

        # Python nor C++ supports partial call natively
        return obj, return_type

    def module(self, obj: ast.Module, **kwargs):
        for expr in obj.body:
            expr, type = self.exec(expr, **kwargs)

    def assign_global(self, expr: ast.Assign):
        type = self.exec(expr.value)
        return expr, type

    def typecheck(self, obj, a, expected_type):
        match = True

        if not match:
            self.diagnostic(obj, f'Typing error {a} != {expected_type}')

        return match

    def annassign_global(self, expr: ast.AnnAssign):
        value, inferred_type = self.exec(expr.value)
        type_constraint = self.exec_type(expr.annotation)

        if not self.typecheck(expr, inferred_type, type_constraint):
            pass

        # Type annotation is user defined and take precedence on the inferred type
        # the reason why is that user can add type annotation to pin point exactly where
        # the mistyping is
        return expr, type_constraint

    def name(self, obj: ast.Name, expected_type=None, **kwargs):
        """
        Examples
        --------
        Guess variable's typing from its value
        >>> import ast
        >>> get_type(
        ...     "a = 1\\n"
        ...     "a\\n"
        ... )
        <class 'int'>
        """
        type = self.typing_context.get(obj.id, None)

        if type is None and expected_type is not None:
            type = expected_type
            self.typing_context[obj.id] = expected_type

        if obj.id in builtintypes:
            return builtintypes[obj.id], TypeType

        if type is None and expected_type is None:
            self.diagnostic(obj, f'Untyped variable {obj.id}')

        return obj, type

    def fetch_type_scope(self, obj):
        if isinstance(obj, CType):
            obj = self.typing_context.get(obj.typename)
            scope = self.scopes.get(obj)
            return scope

    def binop(self, obj: ast.BinOp, **kwargs):
        lhs, lhs_type = self.exec(obj.left, **kwargs)
        scope = self.fetch_type_scope(lhs_type)

        if scope is None:
            self.diagnostic(obj, f'Unable to find context for {lhs_type}')
        else:
            magic_method = operator_magic.get(type(obj.op))
            method_type = scope.get(magic_method)

            if method_type is None:
                self.diagnostic(obj, f'Type {lhs_type} does not have the {type(obj.op)} ({magic_method}) operator')

                for k, v in scope.items():
                    print(f'{k:>30} {v}')

            print(method_type)

        # TODO: check if the operator is supported by that type
        # This is wrong we can expect rhs & lhs to be of a different types
        # we should fetch the function that match and return its return_type
        # similar to what is done in ast.Call
        rhs, rhs_type = self.exec(obj.right, **kwargs)

        if not self.typecheck(obj, rhs_type, expected_type=lhs_type):
            pass

        return obj, rhs_type

    def _return(self, obj: ast.Return, **kwargs):
        _, return_type = self.exec(obj.value, **kwargs)
        meta_type = self.typing_context.get('return')

        if isinstance(meta_type, MetaType):
            meta_type.add_clue(return_type)

        return obj, return_type

    def _import(self, obj: ast.Import, **kwargs):
        # This should fetch the imported element so we can type check its usage
        return obj, None

    def attribute_type(self, obj: ast.Attribute):
        # <value>.<attr>
        value, value_type = self.exec(obj.value)

        # TODO: lookup the type of <attr> in particular
        print('TODO lookup', value_type, pyast.dump(obj.value))
        return value_type

    def attribute(self, obj: ast.Attribute, expected_type=None, **kwargs):
        """
        Examples
        --------
        Guess variable's typing from its value
        >>> import ast
        >>> get_type(
        ...     "class P:\\n"
        ...     "   def __init__(self):\\n"
        ...     "       self.a = 1\\n"
        ...     "p = P()\\n"
        ...     "p.a\\n"
        ... )
        <class 'int'>
        """

        # if expected_type is populated that means we are coming from an assign expression
        # we guessed the type from the value we assigned it to
        attr_type = None
        if not expected_type:
            attr_type = self.attribute_type(obj)

        if expected_type is None:
            expected_type = attr_type

        if expected_type is None:
            self.diagnostic(obj, f'Missing attribute type {pyast.dump(obj)}')

        if self.class_scopes:
            self.class_scopes[-1][obj.attr] = expected_type
            return obj, expected_type

        return obj, expected_type

    def assign(self, obj: ast.Assign, **kwargs):
        # check the value first to guess the type of the target
        _, target_type = self.exec(obj.value, **kwargs)

        target_types = [target_type]
        if len(obj.targets) > 1 and isinstance(target_type, Generic):
            target_types = target_type.types

        for target, expected_type in zip(obj.targets, target_types):
            self.exec(target, expected_type=expected_type, **kwargs)

        return obj, NoneType

    def annassign(self, obj: ast.AnnAssign, expected_type=None, **kwargs):
        expected_type = self.exec_type(obj.annotation, **kwargs)
        expr, expr_type = self.exec(obj.value, expected_type=expected_type, **kwargs)

        if not self.typecheck(obj, expr_type, expected_type):
            pass

        return obj, NoneType

    def exec_type(self, expr, **kwargs):
        mytype, _ = self.exec(expr, **kwargs)

        # string annotation could be a c-string
        if isinstance(mytype, pyast.Str):
            ctype = CType.from_string(mytype.s, self.typing_context)
            return ctype, TypeType

        if isinstance(mytype, pyast.Name):
            return TypeRef(mytype.id), TypeType

        return mytype, TypeType

    def functiondef(self, obj: ast.FunctionDef, **kwargs):
        """
        Examples
        --------
        All types are available, no inference, returns the function type
        >>> import ast
        >>> get_type(
        ... "def add(a: int, b: int) -> int:\\n"
        ... "   return a + b\\n"
        ... )
        typing.Callable[[int, int], int]

        Return type is missing but can be trivially guessed
        >>> import ast
        >>> get_type(
        ... "def add():\\n"
        ... "   return 1\\n"
        ... )
        typing.Callable[[], int]
        """
        return_type, typetype = self.exec_type(obj.returns, **kwargs)

        return_type_inference = MetaType()
        if return_type:
            return_type_inference.add_clue(return_type)

        with self.typing_context as scope:
            scope.name = obj.name
            self.scopes[obj] = scope
            self.function_scopes.append(scope)
            scope['return'] = return_type_inference
            scope['yield'] = return_type_inference

            if obj.name == '__init__' and self.class_name() != '':
                self.init_capture = True

            offset = 0
            args = []

            for arg in obj.args.args[offset:]:
                arg_type = MetaType()
                if arg.annotation is not None:
                    arg_type, typetype = self.exec_type(arg.annotation, **kwargs)

                scope[arg.arg] = arg_type
                args.append(arg_type)

            _, type = self.function_body(obj, **kwargs)

        return_type = return_type_inference.infer()
        # obj.returns = return_type

        fun_type = Callable(args, return_type)
        self.typing_context[obj.name] = fun_type
        self.function_scopes.pop()

        if obj.name == '__init__' and self.class_name() != '':
            self.init_capture = False

        return obj, fun_type

    def function_body(self, obj: ast.FunctionDef, **kwargs):
        body = []
        for b in obj.body:
            self.exec(b, **kwargs)

        return obj.body, None

    def nonetype(self, obj, **kwargs):
        return None, NoneType

    def classdef(self, obj: ast.ClassDef, **kwargs):
        with self.typing_context as scope:
            # ref = Callable[[], None]
            scope.parent[obj.name] = obj

            self.class_scopes.append(scope)
            self.scopes[obj] = scope
            scope.name = obj.name
            scope['self'] = obj

            # need to extract the arguments of the __init__ function
            for b in obj.body:
                self.exec(b, **kwargs)

                # Update the constructor signature
                # if isinstance(method, pyast.FunctionDef) and method.name == '__init__':
                #    ref.__args__ = method_type.__args__

        self.class_scopes.pop()
        return obj, obj


if __name__ == '__main__':
    pass

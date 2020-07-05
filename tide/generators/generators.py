import ast

from tide.generators.visitor import NodeVisitor
from tide.generators.nodes import *
from tide.log import debug, warning


@dataclass
class Type:
    name: str
    ptr: bool


@dataclass
class Entry:
    name: str
    type: Type
    expr: Expression
    newname: Optional[str] = None


TypeType = Type('Type', False)
ModuleType = Type('Module', False)


class MetaVar:
    """Type to be determined"""
    pass


@dataclass
class CppFile:
    modules: List[str]
    imports: List[str]
    body: List[str]

    def gen(self):
        namespaces = '\n'.join([f'namespace {name} {{' for name in self.modules])
        end = '\n'.join([f'}} // {name}' for name in self.modules])

        imps = '\n'.join(self.imports)
        bod = '\n'.join(self.body)
        return f"""
        |{imps}
        |{namespaces}
        |{bod}
        |{end}""".replace('        |', '')


class _Context:
    def __init__(self, parent=None):
        self.old = None
        self.parent = parent
        self.context = dict()

    def __getitem__(self, item):
        v = self.context.get(item)
        if v is not None:
            return v

        if self.parent is not None:
            return self.parent[item]

        raise KeyError(f'key {item} not found')

    def __setitem__(self, key, value):
        self.context[key] = value

    def get(self, name) -> Optional[Entry]:
        return self.context.get(name)


class Context:
    def __init__(self):
        self.ctx = _Context()

    def add(self, name, type, expression, newname=None):
        self.ctx[name] = Entry(name, type, expression, newname)

    def get(self, name, attr, default):
        entry = self.ctx.get(name)
        if entry is None:
            return default
        return getattr(entry, attr)

    def type(self, name) -> Type:
        return self.get(name, 'type', None)

    def expression(self, name) -> Expression:
        return self.get(name, 'expression', None)

    def rename(self, name) -> str:
        return self.get(name, 'newname', name)

    def __enter__(self):
        self.ctx = _Context(self.ctx)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ctx = self.ctx.parent


class GenerateCpp(NodeVisitor):
    def __init__(self, modules=None):
        self.base_indentation = ' ' * 4
        self.indent_level = -1
        self.ctx = Context()
        self.modules = []
        if modules is not None:
            self.modules = modules

    @property
    def indent(self):
        return self.indent_level * self.base_indentation

    def get_typename(self, name):
        if isinstance(name, ast.Name):
            return name.id
        return name

    def get_operator(self, op):
        mapping = {
            ast.Add: '+'
        }
        return mapping[type(op)]

    def generate_inheritance(self, bases: List[Expression]):
        if not bases:
            return ''

        mothers = []
        for b in bases:
            mothers.append(self.get_typename(b))

        mothers = ', '.join(mothers)
        return f': public {mothers}'

    def get_name(self, node: Expression):
        return self.visit(node)

    def process_args(self, args, defaults, cpp_args, templates, depth):
        had_defaults = False
        for i, arg in enumerate(args):
            typename = self.get_typename(arg.annotation)

            if typename is None:
                typename = arg.arg.capitalize()
                templates.append(f'typename {typename}')

            n = len(args) - i
            default = ''
            if len(defaults) >= n:
                had_defaults = True
                default = f' = {self.visit(defaults[-n], depth=depth)}'

            cpp_args.append(f'{typename} {arg.arg}{default}')

        return had_defaults

    def visit_Name(self, node: Name, **kwargs):
        return self.ctx.rename(node.id)

    def visit_BinOp(self, node: BinOp, depth, **kwargs):
        lhs = self.visit(node.left, depth=depth)
        rhs = self.visit(node.right, depth=depth)
        op = self.get_operator(node.op)
        return f'{lhs} {op} {rhs}'

    def visit_Return(self, node: Return, depth, **kwargs):
        if node.value is not None:
            expr = self.visit(node.value, depth=depth)
            return f'return {expr};'

        return 'return;'

    def visit_Num(self, node: ast.Num, **kwargs):
        return node.n

    def visit_Constant(self, node: Constant, **kwargs):
        print(node)
        return node.value

    def visit_Attribute(self, node: Attribute, depth, **kwargs):
        name = self.visit(node.value, depth=depth)

        accessor = '.'
        type = self.ctx.type(name)
        if type and type.ptr:
            accessor = '->'

        return f'{name}{accessor}{node.attr}'

    def visit_AnnAssign(self, node: AnnAssign, **kwargs):
        default = ''
        if node.value is not None:
            default = f' = {node.value}'

        return f'{self.get_typename(node.annotation)} {self.get_name(node.target)}{default};'

    def visit_ClassDef(self, node: ClassDef, depth, **kwargs):
        with self.ctx:
            template = ''

            # Meta class
            # print(node.keywords)

            # Decorators
            struct_type = 'class'
            for d in node.decorator_list:
                d = self.visit(d, depth=depth)
                if d == 'dataclass':
                    struct_type = 'struct'
                else:
                    debug(d)

            body = self.generate_body(node.body, depth, method=True)

            mothers = self.generate_inheritance(node.bases)
            code = f"""{template}
            |{struct_type} {node.name}{mothers} {{
            |    {body}
            |}};
            |""".replace('            |', self.indent)

            # print(code)
            return code

    def visit_arguments(self, args: Arguments, depth, method, **kwargs):
        cpp_args = []
        templates = []

        if method:
            this = args.args[0]
            args.args = args.args[1:]

            # add self as implicit this pointer to the class
            type = Type('self', True)
            self.ctx.add(this.arg, type, this, 'this')

        had_defaults = self.process_args(args.args, args.defaults, cpp_args, templates, depth)
        had_defaults |= self.process_args(args.kwonlyargs, args.kw_defaults, cpp_args, templates, depth)

        if args.kwarg:
            warning('C++ does not support kwargs, kwargs will be inserted into vaarg')

        if had_defaults and args.vararg:
            warning('Cannot add vararg after defaults has been set')

        elif args.vararg:
            typename = args.vararg.arg.capitalize()
            templates.append(f'typename ...{typename}')
            cpp_args.append(f'{typename}... {args.vararg.arg}')

        template = ''
        if templates:
            template = f'template <{", ".join(templates)}>'

        return ', '.join(cpp_args), template

    def visit_ImportFrom(self, import_from: ImportFrom, depth, imports, **kwargs):
        """Convert an import statement to an include

        Example
        -------

        Assume code inside `time` is inside a time namespace (else we cannot support aliasing

        .. code-block:: python

            from time1 import time2 as time3
            # #include <time1>
            # using time3 = time1::time2;

        """
        imports.append(f'#include <{import_from.module}>')

        usings = []
        for alias in import_from.names:
            if alias.asname is None:
                code = f'using {import_from.module}::{alias.name};'
                self.ctx.add(alias.name, MetaVar(), import_from, None)
            else:
                code = f'using {alias.asname} = {import_from.module}::{alias.name};'
                self.ctx.add(alias.name, MetaVar(), import_from, None)

            usings.append(code)

        return '\n'.join(usings)

    def visit_Import(self, import_: Import, depth, imports, **kwargs):
        """Convert an import statement to an include

        Example
        -------

        Assume code inside `time` is inside a time namespace (else we cannot support aliasing

        .. code-block:: python

            import time as t
            # #include <time>
            # using t = time;

        """
        usings = []
        for alias in import_.names:
            # file alias.name should have a namespace alias.name
            # so we can rename it to asname
            imports.append(f'#include <{alias.name}>')

            self.ctx.add(alias.name, ModuleType, import_, None)

            if alias.asname is not None:
                usings.append(f'using {alias.asname} = {alias.name};')
                self.ctx.add(alias.asname, ModuleType, import_, None)

        return '\n'.join(usings)

    def visit_Module(self, module: Module, depth, **kwargs):
        imports = []
        body = self.generate_body(module.body, depth=depth, imports=imports, **kwargs)

        namespaces = '\n'.join([f'namespace {name} {{' for name in self.modules])
        end = '\n'.join([f'}} // {name}' for name in self.modules])

        imports = '\n'.join(imports)
        return f"""
        |{imports}
        |
        |{namespaces}
        |{body}
        |{end}""".replace('        |', '')

    def visit_With(self, node: With, **kwargs):
        print(node.items)

    def generate_body(self, stmts: List[Statement], depth, **kwargs):
        self.indent_level += 1
        body = []
        for stmt in stmts:
            body.append(self.visit(stmt, depth=depth, **kwargs))

        indent = self.indent
        self.indent_level -= 1
        return f'\n{indent}'.join(body)

    def visit_FunctionDef(self, node: FunctionDef, depth, method=False, islambda=False, **kwargs):
        with self.ctx:
            static = ''
            if node.decorator_list:
                for d in node.decorator_list:
                    decorator = self.visit(d, depth=depth)
                    if decorator == 'staticmethod':
                        method = False
                        static = 'static '
                    else:
                        debug(decorator)

            args, template = self.visit(node.args, depth=depth, method=method)

            if islambda:
                body = self.generate_body(node.body, depth, islambda=True)
                code = f"""
                |auto {node.name} = [&]({args}) {{
                |    {body}
                |}};""".replace('                |', self.indent)
            else:
                body = self.generate_body(node.body, depth, islambda=True)
                code = f"""{template}
                |{static}{self.get_typename(node.returns)} {node.name}({args}){{
                |   {body}
                |}}
                |""".replace('                |', self.indent)

            # print(code)
            # self.generic_visit(node)
            return code


import sys
sys.stderr = sys.stdout


data = ast.parse("""
from dataclasses import dataclass
import time

def add(a: int, b: int = 0, *arg, d=2, c=1, **kwargs) -> int:
    return a + b
    
@dataclass
class Point(A, metaclass=ABC):
    x: int
    y: int
    
    def fun(self, a: int, b: int) -> int:
        return self.x + self.y
        
    @staticmethod
    def fun(self, a: int, b: int) -> int:
        def add(a: int, b: int) -> int:
            return a + b

        return self.x + self.y

# with open('file', 'r') as file:
#     n = file.read()
""")


print(data)

visitor = GenerateCpp()
code = visitor.visit(data)

print('----')
print(code)
print('----')





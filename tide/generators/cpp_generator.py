import tide.generators.nodes as ast
import ast as pyast

reserved = {
    'return',
    'import',
    'pass'
}

binop = dict(
    add='+',
    sub='-',
    mult='*'
)


class ProjectFolder:
    """Class helper used to resolve project files"""
    def __init__(self, root):
        self.project_name = root.split('/')[-1]
        self.root = root
        self.prefix = self.root[:-len(self.project_name)]

    def namespaces(self, filename):
        """Transform a filename into a namespace"""
        if filename.startswith(self.prefix):
            return filename[len(self.prefix):].replace('.py', '').split('/'), True

        return filename.replace('.h').split('/'), False

    def module(self, module_path):
        return module_path.replace('.', '/') + '.h'

    def header_guard(self, filename):
        if not filename.startswith(self.root):
            return None

        name = filename[len(self.prefix):]
        return name.replace('.py', '').replace('/', '_').upper() + '_HEADER'


class Stack:
    def __init__(self, s, name):
        self.s = s
        self.name = name

    def __enter__(self):
        self.s.append(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        r = self.s.pop()
        assert r == self.name, 'Nested'


class HeaderGenerator:
    def __init__(self, project: ProjectFolder, filename):
        self.header = []
        self.impl = []

        self.project = project
        self.filename = filename
        namespace, ok = self.project.namespaces(filename)

        self.namespaces = []
        self.namespaced = False
        self.impl_namespaced = False
        self.function_stack = []
        self.class_stack = []
        # are we traversing inside __init__
        self.init_capture = False
        self.body_generation = False
        self.typing = dict()

        if ok:
            self.namespaces = '::'.join(namespace)

    def run(self, module):
        header_guard = self.project.header_guard(self.filename)
        self.header.append(f'#ifndef {header_guard}')
        self.header.append(f'#define {header_guard}\n')

        self.impl.append(f'#include "{self.filename.replace(".py", ".h")}"')

        self.exec(module)

        if self.namespaced:
            self.pop_namespaces()

        if self.impl_namespaced:
            self.pop_impl_namespaces()

        self.header.append(f'#endif')
        return '\n'.join(self.header), '\n'.join(self.impl)

    def push_namespaces(self):
        if not self.namespaces:
            return

        if not self.namespaced:
            self.header.append(f'\nnamespace {self.namespaces} {{\n')
            self.namespaced = True
        else:
            print('Logic Error pushing namespaces when they are already pushed')

    def pop_namespaces(self):
        if not self.namespaces:
            return

        if self.namespaced:
            self.header.append(f'\n}} // {self.namespaces}')
            self.namespaced = False
        else:
            print('Logic Error popping namespaces when they are not pushed')

    def push_impl_namespaces(self):
        if not self.namespaces:
            return

        if not self.impl_namespaced:
            self.impl.append(f'\nnamespace {self.namespaces} {{\n')
            self.impl_namespaced = True
        else:
            print('Logic Error pushing namespaces when they are already pushed')

    def pop_impl_namespaces(self):
        if not self.namespaces:
            return

        if self.impl_namespaced:
            self.impl.append(f'\n}} // {self.namespaces}')
            self.impl_namespaced = False
        else:
            print('Logic Error popping namespaces when they are not pushed')

    @staticmethod
    def _getname(obj):
        name = type(obj).__name__.lower()
        if name in reserved:
            name = '_' + name
        return name

    def exec(self, obj, **kwargs):
        fun = getattr(self, self._getname(obj))
        return fun(obj, **kwargs)

    def _pass(self, obj):
        return ''

    def call(self, obj: ast.Call, **kwargs):
        fun = self.exec(obj.func)
        args = []
        for arg in obj.args:
           args.append(self.exec(arg))
        args = ', '.join(args)

        return f'{fun}({args})'

    def module(self, obj: ast.Module, **kwargs):
        for expr in obj.body:
            self.exec(expr, **kwargs)

    def name(self, obj: ast.Name, **kwargs):
        return obj.id

    def binop(self, obj: ast.BinOp, **kwargs):
        rhs = self.exec(obj.right)
        lhs = self.exec(obj.left)
        op = binop[self._getname(obj.op)]

        return f'{lhs} {op} {rhs}'

    def _return(self, obj: ast.Return, **kwargs):
        val = self.exec(obj.value, **kwargs)
        if not val:
            val = ''

        return 'return ' + val
    
    def _import(self, obj: ast.Import, **kwargs):
        """
        Examples
        --------

        import a.c.d as e
        
        #include "a/b/c.h"
        using e = a::b::c;
        """
        if self.namespaced:
            self.pop_namespaces()

        for alias in obj.names:
            file_name = self.project.module(alias.name)
            self.header.append(f'#include "{file_name}"')

            # this should only be done in cpp files
            # header should not use namespace shortcut to avoid them bleeding out of the project
            if alias.asname is not None:
                importpath = alias.name.replace('.', '::')
                self.header.append(f'using {alias.asname} = {importpath};')
                self.typing[alias.asname] = 'module'

        return

    def is_nested_function(self):
        return len(self.function_stack) > 0

    def is_nested_class(self):
        return len(self.class_stack) > 0

    def is_nested(self):
        return self.is_nested_class() or self.is_nested_function()

    def is_static_method(self, obj: ast.FunctionDef):
        for decorator in obj.decorator_list:
            dec = self.exec(decorator)
            if dec == 'staticmethod':
                return True

        return False

    def argument_offset(self, obj):
        """Ignore the first argument if in class"""
        if self.is_nested_class() and not self.is_static_method(obj):
            return 1
        return 0

    def function_qualifier(self, obj):
        if self.is_static_method(obj):
            return 'static '
        return ''

    def class_name(self):
        if self.class_stack:
            return self.class_stack[-1]
        return ''

    def attribute_accessor(self, name):
        if self.typing[name] == 'module':
            return '::'

        if self.typing[name] == 'pointer':
            return '->'

        return '.'

    def attribute(self, obj: ast.Attribute):
        objexpr = self.exec(obj.value)

        if self.init_capture and objexpr == 'self':
            return obj.attr
        elif objexpr == 'self':
            return f'this->{obj.attr}'

        accessor_op = self.attribute_accessor(objexpr)
        return f'{objexpr}{accessor_op}{obj.attr}'

    def needs_decl(self, names):
        # returns true if they need to be set as variable
        for n in names:
            for acc in ('.', '::', '->'):
                if acc in n:
                    return False
        return True

    def assign(self, obj: ast.Assign):
        if self.init_capture:
            print(f'Type inference not implemented')

            for target in obj.targets:
                name = self.exec(target)
                self.header.append(f'T {name};')
        else:
            names = []
            for target in obj.targets:
                names.append(self.exec(target))
            expr = self.exec(obj.value)

            if len(names) > 1:
                names = ', '.join(names)

                decl = ''
                if self.needs_decl(names):
                    decl = ';\n'.join(['auto ' + n for n in names]) + ';\n'

                return f'{decl}std::tie({names}) = {expr};'

            type = ''
            if self.needs_decl(names):
                type = 'auto'
            return f'{type}{names[0]} = {expr}'

    def annassign(self, obj: ast.AnnAssign):
        name = self.exec(obj.target)
        type = self.exec(obj.annotation)

        if self.init_capture:
            self.header.append(f'{type} {name};')

        else:
            expr = self.exec(obj.value)
            type += ' '
            if not self.needs_decl([name]):
                type = ''
            return f'{type}{name} = {expr}'

    def capture_members(self, obj):
        self.init_capture = True
        for b in obj.body:
            self.exec(b)

        self.header.append("")
        self.init_capture = False

    def functiondef(self, obj: ast.FunctionDef, **kwargs):
        if not self.namespaced:
            self.push_namespaces()

        returntype = self.exec(obj.returns, **kwargs)
        if obj.returns is None:
            returntype = 'void'

        name = obj.name
        with Stack(self.function_stack, name):
            offset = self.argument_offset(obj)

            args = []
            for arg in obj.args.args[offset:]:
                args.append(f'{self.exec(arg.annotation)} {arg.arg}')

            args = ', '.join(args)
            qualifier = self.function_qualifier(obj)

            # Magic functions
            proto_impl = f'{returntype} {name} ({args})'
            class_name = self.class_name()

            if name == '__init__':
                self.capture_members(obj)
                proto_impl = f'{class_name} ({args})'

            elif name == '__del__':
                class_name = self.class_name()
                proto_impl = f'~{class_name} ({args})'

            self.header.append(f'{qualifier}{proto_impl};')

            if class_name:
                class_name = class_name + '::'

            if not self.impl_namespaced:
                self.push_impl_namespaces()

            self.impl.append(f'{class_name}{proto_impl} {{')
            self.function_body(obj, **kwargs)
            self.impl.append('}')

    def depth(self):
        return len(self.function_stack)

    def indent(self):
        return '  ' * self.depth()

    def function_body(self, obj: ast.FunctionDef, **kwargs):
        self.body_generation = True

        body = []
        for b in obj.body:
            a = self.exec(b, **kwargs)

            if a != '':
                body.append(a)

        idt = self.indent()
        if body:
            body = idt + f';\n{idt}'.join(body) + ';'
        else:
            body = ''

        self.impl.append(body)
        self.body_generation = False

    def getinheritance(self, obj):
        bases = []
        for b in obj.bases:
            bases.append(self.exec(b))

        if bases:
            return ': public ' + ', '.join(bases)

        return ''

    def nonetype(self, obj):
        pass

    def classdef(self, obj: ast.ClassDef, **kwargs):
        if not self.namespaced:
            self.push_namespaces()

        name = obj.name
        with Stack(self.class_stack, name):
            bases = self.getinheritance(obj)
            self.header.append(f"struct {name}{bases} {{")

            body = []
            for b in obj.body:
                body.append(self.exec(b))

            self.header.append("};")


if __name__ == '__main__':
    module = pyast.parse("""
    |import myproject.math as math
    |
    |def add(a: float, b: float) -> float:
    |    return math.add(a, b)
    |
    |import myproject.math
    |
    |class Point:
    |   def __init__(self, x: float, y: float):
    |       self.x: float = x
    |       self.y: float = y
    |
    |   def sum(self) -> float:
    |       return self.x + self.y
    |
    |   def __del__(self):
    |       return
    |
    |   def other(self):
    |       pass
    |
    |   @staticmethod
    |   def dist(a: Point, b: Point) -> float:
    |       v = a - b
    |       return sqrt(v * v)
    |
    |""".replace('    |', ''))

    p = ProjectFolder(root='setepenre/work/myproject')
    header, impl = HeaderGenerator(p, 'setepenre/work/myproject/add.py').run(module)
    print(header)
    print('=============')
    print(impl)

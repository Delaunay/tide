import tide.generators.nodes as ast
import ast as pyast

reserved = {
    'return',
    'import',
    'pass',
    'if',
    'raise',
    'while'
}

unaryoperators = {
    'usub': '-'
}

binop = dict(
    add='+',
    sub='-',
    mult='*',
    div='/',
    pow=None
)

compop = {
    'is': '==',
    'lt': '<',
    'gt': '>',
    'lte': '<=',
    'gte': '>=',
    'noteq': '!=',
    'eq': '==',
    'in': None
}

booloperator = {
    'and': '&&',
    'or': '||',
}


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

        return filename.replace('.py', '').split('/'), False

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


class CppGenerator:
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
        self.scope_depth = 0

        if ok:
            self.namespaces = '::'.join(namespace)

    def tuple(self, obj: ast.Tuple, depth, **kwargs):
        elements = []
        for e in obj.elts:
            elements.append(self.exec(e, depth))
        elements = ', '.join(elements)
        return f'std::tuple<>{{{elements}}}'

    def _raise(self, obj: ast.Raise, depth, **kwargs):
        if obj.exc:
            from_exc = self.exec(obj.exc, depth=depth)

        cause = self.exec(obj.cause, depth=depth)
        return f'throw {cause}'

    def num(self, obj: ast.Num, **kwargs):
        return str(obj.n)

    def dict(self, obj: ast.Dict, depth):
        elements = []
        for k, v in zip(obj.keys, obj.values):
            k = self.exec(k, depth)
            v = self.exec(v, depth)
            elements.append(f'{{ {k}, {v} }}')

        elements = ', '.join(elements)
        return f'std::unoredered_map<>{{{elements}}}'

    def augassign(self, obj: ast.AugAssign, depth):
        value = self.exec(obj.value, depth)
        target = self.exec(obj.target, depth)

        op = binop[self._getname(obj.op)]
        return f'{target} {op}= {value}'

    def _if(self, obj: ast.If, depth=0, **kwargs):
        test = self.exec(obj.test, depth)

        base_idt = '  ' * depth
        if_idt = '  ' + base_idt

        body = []
        for b in obj.body:
            body.append(self.exec(b, depth=depth + 1))
        body = f';\n{if_idt}'.join(body)

        orelse = ''
        if obj.orelse:
            orelse = []
            for b in obj.orelse:
                orelse.append(self.exec(b, depth=depth + 1))
            orelse = f';\n{if_idt}'.join(orelse)
            orelse = f' else {{\n{if_idt}{orelse};\n{base_idt}}}'

        return \
     f"""{base_idt}if ({test}) {{
        |{if_idt}{body};
        |{base_idt}}}{orelse}""".replace('        |', '')

    def nameconstant(self, obj: ast.NameConstant, **kwargs):
        if obj.value is True:
            return 'true'

        if obj.value is False:
            return 'false'
        # Bool True/False
        return str(obj.value)

    def unaryop(self, obj: ast.UnaryOp, depth):
        op = unaryoperators[self._getname(obj.op)]
        expr = self.exec(obj.operand, depth)

        return f'{op} {expr}'

    def expr(self, obj: ast.Expr, depth):
        return self.exec(obj.value, depth)

    def compare(self, obj: ast.Compare, depth,**kwargs):
        comp = []
        for b in obj.comparators:
            comp.append(self.exec(b, depth))
        comp = ', '.join(comp)

        left = self.exec(obj.left, depth)

        ops = []
        for o in obj.ops:
            n = self._getname(o)
            op = compop[n]
            ops.append(op)

            if op is None and n == 'in':
                return f'contains({left}, {comp})'

        return f'{comp} {ops[0]} {left}'

    def run(self, module):
        header_guard = self.project.header_guard(self.filename)
        self.header.append(f'#ifndef {header_guard}')
        self.header.append(f'#define {header_guard}\n')

        self.impl.append(f'#include "{self.filename.replace(".py", ".h")}"')

        self.exec(module, depth=0)

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

    def boolop(self, obj: ast.BoolOp, **kwargs):
        op = booloperator[self._getname(obj.op)]
        values = []
        for v in obj.values:
            values.append(self.exec(v, **kwargs))

        return f' {op} '.join(values)

    def subscript(self, obj: ast.Subscript, **kwargs):
        return self.exec(obj.value, **kwargs)

    def set(self, obj: ast.Set, depth, **kwargs):
        elements = []
        for e in obj.elts:
            elements.append(self.exec(e, depth))
        elements = ', '.join(elements)
        return f'std::set<>{elements}'

    def importfrom(self, obj: ast.ImportFrom, **kwargs):
        print('todo')

    def exec(self, obj, depth, **kwargs):
        try:
            fun = getattr(self, self._getname(obj))
            return fun(obj, depth=depth, **kwargs)
        except Exception as e:
            print(f'Error when processing {obj}')

            for c in self.class_stack:
                print('class', c)

            for f in self.function_stack:
                print('function', f)
            raise e

    def _while(self, obj: ast.While, depth, **kwargs):
        test = self.exec(obj.test, depth=depth, **kwargs)
        body = []
        for b in obj.body:
            body.append(self.exec(b, depth=depth + 1, **kwargs))

        idt = '  ' * depth
        body = f';\n  {idt}'.join(body)

        return f"""{idt}while ({test}) {{
        |{idt}{body};
        |}}""".replace('        |', '')

    def str(self, obj: ast.Str, **kwargs):
        return f'"{obj.s}"'

    def _pass(self, obj, **kwargs):
        return ''

    def call(self, obj: ast.Call, **kwargs):
        fun = self.exec(obj.func, **kwargs)
        args = []
        for arg in obj.args:
           args.append(self.exec(arg, **kwargs))
        args = ', '.join(args)

        return f'{fun}({args})'

    def module(self, obj: ast.Module, depth, **kwargs):
        for expr in obj.body:
            self.exec(expr, depth, **kwargs)

    def name(self, obj: ast.Name, **kwargs):
        return obj.id

    def binop(self, obj: ast.BinOp, **kwargs):
        rhs = self.exec(obj.right, **kwargs)
        lhs = self.exec(obj.left, **kwargs)

        n = self._getname(obj.op)
        op = binop[n]

        if op is None:
            if n == 'pow':
                return f'pow({lhs}, {rhs})'

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

    def list(self, obj: ast.List, **kwargs):
        elements = []
        for e in obj.elts:
            elements.append(self.exec(e, **kwargs))
        elements = ', '.join(elements)
        return f'std::vector<>{{{elements}}}'

    def is_nested_function(self):
        return len(self.function_stack) > 0

    def is_nested_class(self):
        return len(self.class_stack) > 0

    def is_nested(self):
        return self.is_nested_class() or self.is_nested_function()

    def is_static_method(self, obj: ast.FunctionDef, **kwargs):
        for decorator in obj.decorator_list:
            dec = self.exec(decorator, **kwargs)
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
        if self.typing.get(name) == 'module':
            return '::'

        if self.typing.get(name) == 'pointer':
            return '->'

        return '.'

    def attribute(self, obj: ast.Attribute, **kwargs):
        objexpr = self.exec(obj.value, **kwargs)

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

    def assign(self, obj: ast.Assign, depth, **kwargs):
        if self.init_capture:
            print(f'Type inference not implemented')

            for target in obj.targets:
                name = self.exec(target, depth)
                self.header.append(f'T {name};')
        else:
            names = []
            for target in obj.targets:
                names.append(self.exec(target, depth))
            expr = self.exec(obj.value, depth)

            if len(names) > 1:
                names = ', '.join(names)

                decl = ''
                if self.needs_decl(names):
                    decl = ';\n'.join(['auto ' + n for n in names]) + ';\n'

                return f'{decl}std::tie({names}) = {expr};'

            type = ''
            if self.needs_decl(names):
                type = 'auto '
            return f'{type}{names[0]} = {expr}'

    def annassign(self, obj: ast.AnnAssign, depth):
        name = self.exec(obj.target, depth)
        type = self.exec(obj.annotation, depth)

        if self.init_capture:
            idt = '  '
            self.header.append(f'{idt}{type} {name};')

        else:
            expr = self.exec(obj.value, depth)
            type += ' '
            if not self.needs_decl([name]):
                type = ''
            return f'{type}{name} = {expr}'

    def capture_members(self, obj, depth):
        self.init_capture = True
        for b in obj.body:
            self.exec(b, depth)

        self.header.append("")
        self.init_capture = False

    def functiondef(self, obj: ast.FunctionDef, depth, **kwargs):
        if not self.namespaced:
            self.push_namespaces()

        returntype = self.exec(obj.returns, depth, **kwargs)
        if obj.returns is None:
            returntype = 'void'

        name = obj.name
        with Stack(self.function_stack, name):
            offset = self.argument_offset(obj)

            args = []
            for arg in obj.args.args[offset:]:
                type = self.exec(arg.annotation, depth)
                if type and type[0] == '"':
                    type = type[1:-1]

                args.append(f'{type} {arg.arg}')

            args = ', '.join(args)
            qualifier = self.function_qualifier(obj)

            # Magic functions
            proto_impl = f'{returntype} {name} ({args})'
            class_name = self.class_name()
            if class_name:
                class_name = '_' + class_name

            if name == '__init__':
                self.capture_members(obj, depth)
                proto_impl = f'{class_name} ({args})'

            elif name == '__del__':
                proto_impl = f'~{class_name} ({args})'

            idt = '  ' * len(self.class_stack)
            self.header.append(f'{idt}{qualifier}{proto_impl};')

            if class_name:
                class_name = class_name + '::'

            if not self.impl_namespaced:
                self.push_impl_namespaces()

            self.impl.append(f'{class_name}{proto_impl} {{')
            self.function_body(obj, depth=depth+1, **kwargs)
            self.impl.append('}')

    def depth(self):
        return len(self.function_stack)

    def indent(self):
        return '  ' * self.depth()

    def function_body(self, obj: ast.FunctionDef, depth, **kwargs):
        self.body_generation = True

        body = []
        for b in obj.body:
            a = self.exec(b, depth, **kwargs)

            if a != '':
                body.append(a)

        idt = self.indent()
        if body:
            body = idt + f';\n{idt}'.join(body) + ';'
        else:
            body = ''

        self.impl.append(body)
        self.body_generation = False

    def getinheritance(self, obj, depth):
        bases = []
        for b in obj.bases:
            bases.append(self.exec(b, depth))

        if bases:
            return ': public ' + ', '.join(bases)

        return ''

    def nonetype(self, obj, **kwargs):
        pass

    def classdef(self, obj: ast.ClassDef, depth, **kwargs):
        """To match Python object behaviour all classes are instantiated as shared pointer"""
        if not self.namespaced:
            self.push_namespaces()

        name = obj.name
        with Stack(self.class_stack, name):
            bases = self.getinheritance(obj, depth)
            self.header.append(f"struct _{name}{bases} {{")

            body = []
            for b in obj.body:
                body.append(self.exec(b, depth=depth + 1))

            self.typing[name] = 'pointer'
            self.typing['_' + name] = 'value'

            self.header.append("};")
            self.header.append(f"using {name} = std::shared_ptr<_{name}>")
            self.header.append(f"""template<class... Args>
            |{name} {name.lower()}(Args&&... args){{
            |   return make_shared<_{name}>(std::forward(args)...);
            |}}""".replace('            |', ''))


class ProjectConverter:
    def __init__(self, root, destination):
        self.project = ProjectFolder(root)
        self.destination = destination

    def run(self):
        import os
        os.makedirs(os.path.join(self.destination, self.project.project_name), exist_ok=True)

        for file in os.listdir(self.project.root):
            with open(os.path.join(self.project.root, file), 'r') as f:
                code = f.read()

            module = pyast.parse(code, filename=file)
            header, impl = CppGenerator(self.project, file).run(module)

            # os.makedirs(os.path.join(self.destination, self.project.project_name, file), exist_ok=True)

            path = os.path.join(self.destination, self.project.project_name)
            with open(os.path.join(path, file.replace('.py', '.cpp')), 'w') as implfile:
                implfile.write(impl)

            with open(os.path.join(path, file.replace('.py', '.h')), 'w') as headerfile:
                headerfile.write(header)


if __name__ == '__main__':
    converter = ProjectConverter(
        'C:/Users/Newton/work/tide/examples/symdiff',
        'C:/Users/Newton/work/tide/examples/symdiff_cpp')

    converter.run()

    # module = pyast.parse("""""".replace('    |', ''))
    #
    # p = ProjectFolder(root='setepenre/work/myproject')
    # header, impl = CppGenerator(p, 'setepenre/work/myproject/add.py').run(module)
    # print(header)
    # print('=============')
    # print(impl)

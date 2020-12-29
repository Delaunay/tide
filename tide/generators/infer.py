import ast as pyast
from typing import *

import tide.generators.nodes as ast
from tide.generators.utils import ProjectFolder, Stack


class KiwiType:
    pass


NoneType = KiwiType


class StructType(KiwiType):
    def __init__(self, types):
        self.types = types


class UnionType(KiwiType):
    def __init__(self, types):
        self.types = types


class TypeInference:
    def __init__(self, project: ProjectFolder, filename):
        self.project = project
        self.filename = filename

    def tuple(self, obj: ast.Tuple, **kwargs):
        types = []
        for e in obj.elts:
            value, type = self.exec(e, **kwargs)
            types.append(type)

        return obj, Tuple[*types]

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
            _, type = self.exec(e, **kwargs)
            types.append(type)

        first = types[0]
        for type in types:
            if isinstance(type, isinstance(first)):
                print(f'warning type mismatch {type} != {first}')

        return obj, first

    def set(self, obj: ast.Set, **kwargs):
        _, t = self.infer_container(obj, **kwargs)
        return obj, Set[t]

    def list(self, obj: ast.List, **kwargs):
        _, t = self.infer_container(obj, **kwargs)
        return obj, List[t]

    def dict(self, obj: ast.Dict, **kwargs):
        elements = []
        for k, v in zip(obj.keys, obj.values):
            k = self.exec(k, **kwargs)
            v = self.exec(v, **kwargs)
            elements.append(f'{{ {k}, {v} }}')

        elements = ', '.join(elements)
        return f'std::make_dict{{{elements}}}'

    def augassign(self, obj: ast.AugAssign, **kwargs):
        value = self.exec(obj.value, **kwargs)
        target = self.exec(obj.target, **kwargs)

        op = binop[self._getname(obj.op)]
        return f'{target} {op}= {value}'

    def _if(self, obj: ast.If, **kwargs):
        test = self.exec(obj.test, **kwargs)

        depth = kwargs.get('depth', 0)
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


    def unaryop(self, obj: ast.UnaryOp, **kwargs):
        op = unaryoperators[self._getname(obj.op)]
        expr = self.exec(obj.operand, **kwargs)

        return f'{op} {expr}'

    def expr(self, obj: ast.Expr, **kwargs):
        return self.exec(obj.value, **kwargs)

    def compare(self, obj: ast.Compare, **kwargs):
        depth = kwargs.get('depth', 0)
        comp = []
        for b in obj.comparators:
            comp.append(self.exec(b, **kwargs))
        comp = ', '.join(comp)

        left = self.exec(obj.left, **kwargs)

        ops = []
        for o in obj.ops:
            n = self._getname(o)
            op = compop[n]
            ops.append(op)

            if op is None and n == 'in':
                return f'contains({left}, {comp})'

        return f'{left} {ops[0]} {comp}'

    def run(self, module):
        self.exec(module, depth=0)

    def boolop(self, obj: ast.BoolOp, **kwargs):
        return obj, bool

    def subscript(self, obj: ast.Subscript, **kwargs):
        return self.exec(obj.value, **kwargs)

    def importfrom(self, obj: ast.ImportFrom, **kwargs):
        libname = self.project.module(obj.module, level=obj.level)
        if libname:
            self.header.append(f'#include {libname}')

    def exec(self, obj, **kwargs):
        try:
            fun = getattr(self, self._getname(obj))
            return fun(obj, **kwargs)
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
        |{idt}}}""".replace('        |', '')

    def _pass(self, obj, **kwargs):
        return obj, None

    def call(self, obj: ast.Call, **kwargs):
        fun = self.exec(obj.func, **kwargs)
        args = []
        for arg in obj.args:
            args.append(self.exec(arg, **kwargs))
        args = ', '.join(args)

        return f'{fun}({args})'

    def module(self, obj: ast.Module, **kwargs):
        def main_guard(expr):
            if isinstance(expr.test, pyast.Compare):
                comp: ast.Compare = expr.test
                op = comp.ops[0]
                name = comp.left
                value = comp.comparators[0]

                comparing_op = isinstance(op, pyast.Eq)
                comparing_name = isinstance(name, pyast.Name) and name.id == '__name__'
                comparing_main = isinstance(value, pyast.Str) and value.s == '__main__'

                return comparing_name and comparing_main and comparing_op

            return False

        for expr in obj.body:
            top_level_expr = self.exec(expr, **kwargs)

            # Make a new entry-point
            if isinstance(expr, pyast.If) and main_guard(expr):
                if len(expr.orelse) > 0:
                    print('Warning ignoring the else when generating a new entry point')

                self.entry_point(expr.body)

            elif isinstance(expr, pyast.Assign):
                self.assign_global(expr)

            elif isinstance(expr, pyast.AnnAssign):
                self.annassign_global(expr)

            elif top_level_expr != '' and top_level_expr is not None:

                print(f'Generating init script {expr}')
                self.module_init([])

    def assign_global(self, expr: ast.Assign):
        print('inference is not implemented')
        name = self.exec(expr.targets[0])
        value = self.exec(expr.value)

        self.header.append(f'extern auto {name};')
        self.impl.append(f'auto {name} = {value};')
        return

    def annassign_global(self, expr: ast.AnnAssign):
        name = self.exec(expr.target)
        value = self.exec(expr.value)
        type = self.exec_type(expr.annotation)

        self.header.append(f'extern {type} {name};')
        self.impl.append(f'{type} {name} = {value};')
        return

    def name(self, obj: ast.Name, **kwargs):
        if self.class_name() != '' and obj.id == 'self':
            return 'this'

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
        _, type = self.exec(obj.value, **kwargs)
        return obj, type

    def _import(self, obj: ast.Import, **kwargs):
        """
        Examples
        --------

        import a.c.d as e

        #include "a/b/c.h"
        using e = a::b::c;
        """
        for alias in obj.names:
            file_name = self.project.module(alias.name)
            if file_name != '':
                self.header.append(f'#include {file_name}')

                # this should only be done in cpp files
                # header should not use namespace shortcut to avoid them bleeding out of the project
                if alias.asname is not None:
                    importpath = alias.name.replace('.', '::')
                    self.header.append(f'using {alias.asname} = {importpath};')
                    self.typing[alias.asname] = 'module'

        return

    def function_qualifier(self, obj, **kwargs):
        if self.is_static_method(obj, **kwargs):
            return 'static '

        # all functions are virtual in python
        class_name = self.class_name()
        if class_name and obj.name != '__init__' and self.is_virtual(obj, **kwargs):
            return 'virtual '

        return ''

    def attribute(self, obj: ast.Attribute, **kwargs):
        objexpr = self.exec(obj.value, **kwargs)

        if self.init_capture and objexpr == 'this':
            return obj.attr
        elif objexpr == 'self':
            return f'this->{obj.attr}'

        accessor_op = self.attribute_accessor(objexpr)
        return f'{objexpr}{accessor_op}{obj.attr}'

    def assign(self, obj: ast.Assign, **kwargs):
        if self.init_capture:
            print(f'Type inference not implemented')

            for target in obj.targets:
                name = self.exec(target, **kwargs)
                self.header.append(f'T {name};')
        else:
            names = []
            for target in obj.targets:
                names.append(self.exec(target, **kwargs))
            expr = self.exec(obj.value, **kwargs)

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

    def annassign(self, obj: ast.AnnAssign, **kwargs):
        name = self.exec(obj.target, **kwargs)
        type = self.exec_type(obj.annotation, **kwargs)

        if self.init_capture:
            idt = '  '
            self.header.append(f'{idt}{type} {name};')

        else:
            expr = self.exec(obj.value, **kwargs)
            type += ' '
            if not self.needs_decl([name]):
                type = ''
            return f'{type}{name} = {expr}'

    def exec_type(self, expr, **kwargs):
        v = self.exec(expr, **kwargs)

        if v is None:
            return 'void'

        if v and v[0] == '"':
            v = v[1:-1]

        return v

    def functiondef(self, obj: ast.FunctionDef, depth, **kwargs):
        pass

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

    def nonetype(self, obj, **kwargs):
        return None, NoneType

    def classdef(self, obj: ast.ClassDef, depth, **kwargs):
        """To match Python object behaviour all classes are instantiated as shared pointer"""
        if not self.namespaced:
            self.push_namespaces()

        config = self.class_config(obj)

        name = obj.name
        with Stack(self.class_stack, name):
            bases = self.getinheritance(obj, **kwargs)
            # Forward declaration
            # self.header.append(f"struct _{name};")
            # self.header.append(f"using {name} = std::shared_ptr<_{name}>;")
            self.header.append(f"struct {name}{bases} {{")

            body = []
            for b in obj.body:
                body.append(self.exec(b, depth=depth + 1, classconfig=config, **kwargs))

            # self.typing[name] = 'pointer'
            self.typing[name] = 'value'

            self.header.append("};")
            # self.header.append(f"""template<class... Args>
            # |{name} {name.lower()}(Args&&... args){{
            # |   return std::make_shared<_{name}>(std::forward(args)...);
            # |}}""".replace('            |', ''))


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

            path = os.path.join(self.destination, self.project.project_name)
            with open(os.path.join(path, file.replace('.py', '.cpp')), 'w') as implfile:
                implfile.write(impl)

            with open(os.path.join(path, file.replace('.py', '.h')), 'w') as headerfile:
                headerfile.write(header)


if __name__ == '__main__':
    pass
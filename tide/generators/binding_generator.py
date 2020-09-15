import clang.cindex
from clang.cindex import Cursor, CursorKind, Type, SourceLocation, TypeKind

from tide.generators.api_generators import show_elem, get_comment, type_mapping
import tide.generators.nodes as T
import ctypes

import ast
from ast import Module
import logging
from astunparse import unparse, dump


log = logging.getLogger('TIDE')


def is_valid(name):
    # flag something like below as invalid
    # union SDL_GameControllerButtonBind::(anonymous at /usr/include/SDL2/SDL_gamecontroller.h:75:5)
    return not all(c in name for c in (':', '(', '.', ' '))


def d(depth=0):
    s = '|:' * depth
    return s + '-> '


def get_typename(type: Type) -> T.Name:
    if not type.is_const_qualified():
        return T.Name(type.spelling)

    typename = type.spelling.replace('const ', '')
    return T.Name(typename)


class Unsupported(Exception):
    pass


class APIGenerator:
    def __init__(self):
        self.type_registry = type_mapping()

    def generate_type(self, type, depth=0):
        if type.spelling == 'va_list':
            raise Unsupported()

        lookup_name = type.spelling
        if type.is_const_qualified():
            lookup_name = lookup_name.replace('const', '').strip()

        # This is meant to remember typedefs and use the typedef instead of the underlying type
        # In particular when `typedef struct` is used
        cached_type = self.type_registry.get(lookup_name)
        if cached_type is not None:
            log.debug(f'{d(depth)}Found cached type `{cached_type}`')
            return cached_type

        val = self._generate_type(type, depth)
        self.type_registry[type.spelling] = val
        log.debug(f'{d(depth)}Resolved type `{type.spelling}` to `{val}`')
        return val

    def _generate_type(self, type: Type, depth=0):
        # print(type.kind, type.spelling, self.type_registry.get(type.spelling, 'NOT FOUND'))
        if type.kind == TypeKind.VOID:
            return T.Name('None')

        if type.kind == TypeKind.POINTER and type.get_pointee().kind == TypeKind.VOID:
            return T.Name('c_void_p')

        if type.kind == TypeKind.POINTER and type.get_pointee().kind == TypeKind.CHAR_S:
            return T.Name('c_char_p')

        if type.kind == TypeKind.POINTER:
            pointee: Type = type.get_pointee()

            # Typedef use the name that it is aliased to
            if pointee.kind is TypeKind.TYPEDEF:
                pointee = get_typename(pointee)

            elif pointee.kind != TypeKind.VOID:
                pointee = self.generate_type(pointee, depth + 1)
            else:
                pointee = T.Name('c_void_p')

            # Function pointer do not need to be decorated by POINTER call
            if isinstance(pointee, T.Call) and isinstance(pointee.func, T.Name) and pointee.func.id == 'CFUNCTYPE':
                return pointee

            # for native types we need to keep ref because python will copy them
            return T.Call(T.Name('POINTER'), [pointee])

        if type.kind == TypeKind.CHAR_S:
            return T.Name('c_char_p')

        # if type.is_const_qualified():
        #     return T.Name(get_typename(type))

        if type.kind == TypeKind.TYPEDEF:
            return get_typename(type)

        if type.kind == TypeKind.FUNCTIONPROTO or (type.kind == TypeKind.UNEXPOSED and type.get_canonical().kind == TypeKind.FUNCTIONPROTO):
            # SDL_HitTest = CFUNCTYPE(SDL_HitTestResult, POINTER(SDL_Window), POINTER(SDL_Point), c_void_p)
            canon = type
            if type.kind == TypeKind.UNEXPOSED:
                canon = type.get_canonical()

            rtype = canon.get_result()

            args = []
            for arg in canon.argument_types():
                args.append(self.generate_type(arg, depth + 1))

            returntype = self.generate_type(rtype, depth + 1)

            cargs = [returntype]
            cargs.extend(args)
            return T.Call(T.Name('CFUNCTYPE'), args=cargs)

        if type.kind == TypeKind.CONSTANTARRAY:
            t = self.generate_type(type.element_type, depth + 1)
            return T.BinOp(t, ast.Mult(), T.Constant(type.element_count))

        # Represents a C array with an unspecified size.
        if type.kind == TypeKind.INCOMPLETEARRAY:
            element_type = self.generate_type(type.element_type, depth + 1)
            # char *[] -> char **
            return T.Call(T.Name('POINTER'), [element_type])

        # struct <TYPENAME>
        if type.kind == TypeKind.ELABORATED:
            return T.Name(get_typename(type).id.replace('struct', '').strip())

        if type.kind == TypeKind.ENUM:
            return get_typename(type)

        show_elem(type)
        return get_typename(type)

    def generate_function(self, elem: Cursor, depth=0):
        log.debug(f'{d(depth)}Generate function `{elem.spelling}`')
        definition: Cursor = elem.get_definition()

        if definition is None:
            definition = elem

        rtype = self.generate_type(definition.result_type, depth + 1)
        args = definition.get_arguments()

        pyargs = []
        for a in args:
            atype = self.generate_type(a.type, depth + 1)
            pyargs.append(atype)

        funnane = definition.spelling
        if not pyargs:
            pyargs = T.Name('None')
        else:
            pyargs = T.List(elts=pyargs)

        binding_call = T.Call(T.Name('_bind'), [T.Str(funnane), pyargs, rtype])
        return T.Assign([T.Name(funnane)], binding_call)

    def get_name(self, elem, rename=None, depth=0):
        log.debug(f'{d(depth)}Fetch name')
        pyname = elem.spelling

        if hasattr(elem, 'displayname') and elem.displayname:
            pyname = elem.displayname

        # Typedef or anonymous struct/union
        if not pyname:
            pyname = elem.type.spelling

        if rename is not None and hasattr(elem, 'get_usr') and elem.get_usr() in rename:
            parent, name = rename[elem.get_usr()]
            return name

        if not is_valid(pyname):
            pyname = ''

        return pyname

    def find_anonymous_fields(self, elem, parent='', depth=0):
        # Find Anonymous struct or union
        # to rename them so something valid
        # Those are also nested struct
        anonymous = dict()
        anonymous_renamed = dict()

        for attr in elem.get_children():
            if attr.kind == CursorKind.UNION_DECL or attr.kind == CursorKind.STRUCT_DECL:
                attr_type_name = self.get_name(attr, depth=depth + 1)
                log.debug(f'{d(depth)}Found nested decl, {attr.kind} {attr.spelling} {attr_type_name}')
                anonymous[attr.get_usr()] = attr

            if attr.kind == CursorKind.FIELD_DECL:
                usr = self.get_underlying_type_uid(attr.type)
                log.debug(f'{d(depth)} attr, {attr.kind} {attr.spelling} {usr}')

                if usr in anonymous:
                    log.debug(f'{d(depth)}Found attribute using nested decl: {attr.kind} {attr.spelling}')

                    name = '_' + self.get_name(attr, depth=depth + 1).capitalize()
                    anonymous_renamed[usr] = (parent, name)

        return anonymous_renamed

    def get_underlying_type_uid(self, type: Type):
        if type.kind == TypeKind.POINTER:
            return self.get_underlying_type_uid(type.get_pointee())

        if type.kind == TypeKind.TYPEDEF:
            return type.get_declaration().get_usr()

        if type.kind == TypeKind.ELABORATED:
            show_elem(type)
            print(type.get_declaration().get_usr())
            return type.get_declaration().get_usr()

        return type.get_declaration().get_usr()

    def generate_field(self, body, attrs, attr, anonymous_renamed, depth):
        if attr.kind == CursorKind.FIELD_DECL:
            # Rename anonymous types
            uid = self.get_underlying_type_uid(attr.type)

            log.debug(f'{d(depth)}uid: {uid} {attr.type.spelling} {anonymous_renamed}')
            if uid in anonymous_renamed:
                parent, name = anonymous_renamed[uid]
                if parent:
                    typename = T.Attribute(T.Name(parent), name)
                else:
                    typename = T.Name(name)

                if attr.type.kind == TypeKind.POINTER:
                    typename = T.Call(T.Name('POINTER'), [typename])
            else:
                typename = self.generate_type(attr.type, depth + 1)

            pair = T.Tuple()
            pair.elts = [
                T.Str(attr.spelling),
                typename
            ]
            attrs.elts.append(pair)

        elif attr.kind in (CursorKind.UNION_DECL, CursorKind.STRUCT_DECL):
            nested_struct = self.generate_struct_union(
                attr,
                depth + 1,
                nested=True,
                rename=anonymous_renamed)

            body.append(nested_struct)
        elif attr.kind == CursorKind.PACKED_ATTR:
            for attr2 in attr.get_children():
                self.generate_field(body, attrs, attr2, anonymous_renamed, depth + 1)
                # attrs.append(field)
        else:
            show_elem(attr)
            print('NESTED ', attr.kind)
            raise RuntimeError('')

    def generate_struct_union(self, elem: Cursor, depth=1, nested=False, rename=None):
        log.debug(f'{d(depth)}Generate struct `{elem.spelling}`')
        pyname = self.get_name(elem, rename=rename, depth=depth + 1)

        base = 'Structure'
        if elem.kind == CursorKind.UNION_DECL:
            base = 'Union'

        # For recursive data structure
        #  log.debug(pyname)
        self.type_registry[f'struct {pyname}'] = T.Name(pyname)
        self.type_registry[f'const struct {pyname}'] = T.Name(pyname)

        parent = pyname
        anonymous_renamed = self.find_anonymous_fields(elem, parent, depth=depth + 1)

        # Docstring is the first element of the body
        # T.Constant(get_comment(elem))
        body = []
        attrs = T.List()

        attr: Cursor
        for attr in elem.get_children():
            self.generate_field(body, attrs, attr, anonymous_renamed, depth)

        # fields are at the end because we might use types defined above
        if not body:
            body.append(ast.Pass())

        if not attrs.elts:
            return T.ClassDef(name=pyname, bases=[T.Name(base)], body=body)

        fields = T.Assign([T.Attribute(T.Name(pyname), '_fields_')], attrs)
        return [T.ClassDef(name=pyname, bases=[T.Name(base)], body=body), fields]

    def generate_enum(self, elem: Cursor, depth=0):
        log.debug(f'{d(depth)}Generate Enum')
        name = self.get_name(elem)

        enum = []

        if name:
            enum.append(T.Assign([T.Name(name)], self.type_registry.get('int')))

        for value in elem.get_children():
            if value.kind == CursorKind.ENUM_CONSTANT_DECL:
                enum.append(T.Assign(
                    [T.Name(self.get_name(value))],
                    T.Constant(value.enum_value)))
            else:
                log.error(f'Unexpected children {value.kind}')
                raise RuntimeError()

        return enum

    def dispatch(self, elem):
        if elem.kind == CursorKind.FUNCTION_DECL:
            return self.generate_function(elem)

        elif elem.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL):
            return self.generate_struct_union(elem)

        elif elem.kind == CursorKind.TYPEDEF_DECL:
            t1 = elem.type
            t2 = elem.underlying_typedef_type

            log.debug(f'Typedef {t1.spelling} = {t2.spelling}')
            # SDL_version = struct SDL_version
            if t1.spelling == t2.spelling.split(' ')[-1]:
                if t2.spelling not in self.type_registry:
                    self.type_registry[t2.spelling] = T.Name(t1.spelling, ctx=ast.Load())
                return None

            t2type: T.Name = self.generate_type(t2)
            if t2.spelling not in self.type_registry:
                self.type_registry[t2.spelling] = T.Name(t1.spelling, ctx=ast.Load())

            expr = ast.Assign([T.Name(t1.spelling, ctx=ast.Store())], t2type)
            return expr

        elif elem.kind == CursorKind.ENUM_DECL:
            return self.generate_enum(elem)

        # Global variables
        elif elem.kind == CursorKind.VAR_DECL:
            print(f'{elem.spelling}: {self.generate_type(elem.type)}')
        else:
            show_elem(elem)

    def generate(self, tu):
        module: T.Module = Module()
        module.body = []

        elem: Cursor
        for elem in tu.cursor.get_children():
            loc: SourceLocation = elem.location

            if not str(loc.file.name).startswith('/usr/include/SDL2'):
               continue

            try:
                expr = self.dispatch(elem)

                if expr is not None and not isinstance(expr, str):

                    if isinstance(expr, list):
                        for e in expr:
                            module.body.append(T.Expr(e))
                    else:
                        module.body.append(T.Expr(expr))

            except Unsupported:
                pass

        return module


if __name__ == '__main__':
    import sys
    logging.basicConfig(stream=sys.stdout)
    log.setLevel(logging.DEBUG)

    index = clang.cindex.Index.create()
    file = '/usr/include/SDL2/SDL.h'
    # file = '/home/setepenre/work/tide/tests/binding/typedef_func.h'
    # file = '/home/setepenre/work/tide/tests/binding/nested_struct.h'
    tu = index.parse(file)

    for diag in tu.diagnostics:
        print(diag.format())

    gen = APIGenerator()
    module = gen.generate(tu)

    print('=' * 80)

    import os
    dirname = os.path.dirname(__file__)

    with open(os.path.join(dirname, '..', '..', 'output', 'sdl2.py'), 'w') as f:
        f.write("""import os\n""")
        f.write("""from ctypes import *\n""")
        f.write("""from tide.runtime.loader import DLL\n""")
        f.write("""_lib = DLL("SDL2", ["SDL2", "SDL2-2.0"], os.getenv("PYSDL2_DLL_PATH"))\n""")
        f.write("""_bind = _lib.bind_function\n""")
        f.write(unparse(module))

    import pprint
    # pprint.pprint(gen.type_registry)

    # import ast
    # ast.dump(module)

    # from ast import FunctionDef, Pass
    #
    # class_def = T.ClassDef(name='MyClass')
    #
    # method = T.FunctionDef('MyFun')
    # method.body = [Pass()]
    # method.args = T.Arguments(
    #     args=[T.Arg(arg='self', annotation=T.Name('MyClass'))],
    # )
    #
    # class_def.body.append(method)
    # module: T.Module = Module()
    # module.body = [class_def]

    import ast
    mod = ast.parse("""
class check:
    \"\"\"ABC\"\"\"
    pass

a = check
    """)

    print(dump(mod))
    print(unparse(mod))


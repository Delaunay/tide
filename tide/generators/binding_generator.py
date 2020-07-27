import clang.cindex
from clang.cindex import Cursor, CursorKind, Type, SourceLocation, TypeKind

from tide.generators.api_generators import show_elem
import tide.generators.nodes as T
import ctypes

from ast import ClassDef
from copy import deepcopy
from ast import Module

# type_mapping = dict(
#     int8_t=ctypes.c_int8,
#     uint8_t=ctypes.c_uint8,
#     int16_t=ctypes.c_uint64,
#     uint16_t=ctypes.c_uint64,
#     int32_t=ctypes.c_uint64,
#     uint32_t=ctypes.c_uint64,
#     int64_t=ctypes.c_uint64,
#     uint64_t=ctypes.c_uint64
# )

type_mapping = dict(
    int8_t='c_int8',
    uint8_t='c_uint8',
    int16_t='c_uint64',
    uint16_t='c_uint64',
    int32_t='c_uint64',
    uint32_t='c_uint64',
    int64_t='c_uint64',
    uint64_t='c_uint64'
)


def reformat_comment(comment):
    return (comment
            # Beginning of comment
            .replace('/**', '')
            # Start og paragraph
            .replace(' *  ', '    ')
            # End
            .replace('*/', '').strip()
            # Empty Line
            .replace(' *', '    '))


def get_comment(elem, indent='    '):
    comment = ''
    if elem.raw_comment:
        comment = f'{indent}"""{reformat_comment(elem.raw_comment)}"""\n'
    return comment


def is_valid(name):
    # flag something like below as invalid
    # union SDL_GameControllerButtonBind::(anonymous at /usr/include/SDL2/SDL_gamecontroller.h:75:5)
    return not all(c in name for c in (':', '(', '.', ' '))


class APIGenerator:
    def __init__(self):
        self.type_registry = deepcopy(type_mapping)

    def generate_type(self, type):
        # This is meant to remember typedefs and use the typedef instead of the underlying type
        # In particular when `typedef struct` is used
        if type.spelling in self.type_registry:
            return self.type_registry[type.spelling]

        val = self._generate_type(type)
        self.type_registry[type.spelling] = val
        return val

    def _generate_type(self, type: Type, depth=0):
        if type.kind == TypeKind.VOID:
            return 'None'

        if type.kind == TypeKind.POINTER and type.get_pointee().kind == TypeKind.VOID:
            return 'any'

        if type.kind == TypeKind.POINTER:
            pointee: Type = type.get_pointee()
            if pointee.kind is TypeKind.TYPEDEF:
                pointee = pointee.get_canonical()

            # in python every object is a pointer
            if pointee.kind in (TypeKind.RECORD, TypeKind.FUNCTIONPROTO, TypeKind.UNEXPOSED):
                return self._generate_type(pointee, depth + 1)

            if not pointee.is_pod():
                show_elem(pointee)

            # for native types we need to keep ref because python will copy them
            return f'Ref[{self._generate_type(pointee, depth + 1)}]'

        if type.kind == TypeKind.CHAR_S:
            return 'str'

        if type.is_const_qualified():
            typename = type.spelling.replace('const ', '')
            return f'Const[{typename}]'

        if type.kind == TypeKind.TYPEDEF:
            return type.spelling

        if type.kind == TypeKind.FUNCTIONPROTO or (type.kind == TypeKind.UNEXPOSED and type.get_canonical().kind == TypeKind.FUNCTIONPROTO):
            canon = type.get_canonical()
            rtype = canon.get_result()

            args = []
            for arg in canon.argument_types():
                args.append(self._generate_type(arg, depth + 1))

            args = ', '.join(args)
            # show_elem(type.get_canonical())
            return f'Callable[[{args}], {self._generate_type(rtype, depth + 1)}]'

        # show_elem(type)
        return type.spelling

    def generate_function(self, elem: Cursor):
        definition: Cursor = elem.get_definition()

        if definition is None:
            definition = elem

        pyargs = []

        rtype = self.generate_type(definition.result_type)
        args = definition.get_arguments()

        for a in args:
            atype = self.generate_type(a.type)
            aname = a.displayname
            pyargs.append(f'{aname}: {atype}')

        funnane = definition.spelling
        pyargs = ', '.join(pyargs)

        comment = get_comment(elem)
        return f'\ndef {funnane}({pyargs}) -> {rtype}:\n{comment}    pass\n'

    def get_name(self, elem, rename=None):
        pyname = elem.spelling

        if hasattr(elem, 'displayname') and elem.displayname:
            pyname = elem.displayname

        # Typedef or anonymous struct/union
        if not pyname:
            pyname = elem.type.spelling

        if rename is not None and hasattr(elem, 'get_usr') and elem.get_usr() in rename:
            return rename[elem.get_usr()]

        if not is_valid(pyname):
            pyname = ''

        return pyname

    def find_anonymous_fields(self, elem):
        # Find Anonymous struct or union
        # to rename them so something valid
        anonymous = dict()
        anonymous_renamed = dict()

        for attr in elem.get_children():
            if attr.kind == CursorKind.UNION_DECL or attr.kind == CursorKind.STRUCT_DECL:
                attr_type_name = self.get_name(attr)
                if not attr_type_name:
                    anonymous[attr.get_usr()] = attr

            if attr.kind == CursorKind.FIELD_DECL:
                usr = attr.type.get_declaration().get_usr()
                if usr in anonymous:
                    anonymous_renamed[usr] = '_' + self.get_name(attr).capitalize()

        return anonymous_renamed

    def generate_struct_union(self, elem: Cursor, depth=1, nested=False, rename=None):
        pyname = self.get_name(elem, rename=rename)

        base = 'Structure'
        if elem.kind == CursorKind.UNION_DECL:
            base = 'Union'

        anonymous_renamed = self.find_anonymous_fields(elem)

        body = []
        attrs = T.List()

        attr: Cursor
        for attr in elem.get_children():
            if attr.kind == CursorKind.FIELD_DECL:
                # Rename anonymous types
                uid = attr.type.get_declaration().get_usr()

                if uid in anonymous_renamed:
                    typename = anonymous_renamed[uid]
                else:
                    typename = self.generate_type(attr.type)

                pair = T.Tuple()
                pair.elts = [
                    T.Str(attr.spelling),
                    T.Name(typename)
                ]
                attrs.elts.append(pair)

            elif attr.kind in (CursorKind.UNION_DECL, CursorKind.STRUCT_DECL):
                nested_struct = self.generate_struct_union(
                    attr,
                    depth + 1,
                    nested=True,
                    rename=anonymous_renamed)

                body.append(nested_struct)
            else:
                print('NESTED ', attr.kind)

        # fields are at the end because we might use types defined above
        body.append(T.Assign([T.Name('_fields_')], attrs))
        return T.ClassDef(
            name=pyname,
            bases=[T.Name(base)],
            body=body,
        )

    def generate_enum(self, elem: Cursor):
        name = self.get_name(elem)

        values = []
        for value in elem.get_children():
            if value.kind == CursorKind.ENUM_CONSTANT_DECL:
                values.append(f'{self.get_name(value)} = {value.enum_value}')
            else:
                print('ERROR')
                show_elem(value)

        values = '\n'.join(values)
        return f"\nclass {name}(enum):\n    pass\n\n{values}\n"

    def dispatch(self, elem):
        if elem.kind == CursorKind.FUNCTION_DECL:
            return self.generate_function(elem)
            print(fun)

        elif elem.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL):
            return self.generate_struct_union(elem)

        elif elem.kind == CursorKind.TYPEDEF_DECL:
            t1 = elem.type
            t2 = elem.underlying_typedef_type

            # SDL_version = struct SDL_version
            if t1.spelling == t2.spelling.split(' ')[-1]:
                self.type_registry[t2.spelling] = t1.spelling
                return None

            t2type = self.generate_type(t2)
            self.type_registry[t2type] = t1.spelling
            return T.Assign([T.Name(t1.spelling)], T.Name(t2type))

        elif elem.kind == CursorKind.ENUM_DECL:
            enum = self.generate_enum(elem)
            print(enum)

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

            expr = self.dispatch(elem)

            if expr is not None and not isinstance(expr, str):
                module.body.append(expr)

        return module


if __name__ == '__main__':
    index = clang.cindex.Index.create()
    tu = index.parse('/usr/include/SDL2/SDL.h')

    gen = APIGenerator()
    module = gen.generate(tu)

    print('=' * 80)
    from astunparse import unparse
    print(unparse(module))

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
    #
    #
    #
    #

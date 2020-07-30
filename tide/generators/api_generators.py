import clang.cindex
from clang.cindex import Cursor, CursorKind, Type, SourceLocation, TypeKind

import tide.generators.nodes as T
from astunparse import unparse


def type_mapping():
    return {
        'int': T.Name('c_int'),
        'unsigned int': T.Name('c_uint'),
        'long': T.Name('c_long'),
        'unsigned long': T.Name('c_ulong'),
        'unsigned char': T.Name('c_ubyte'),
        'unsigned short': T.Name('c_ushort'),
        'short': T.Name('c_short'),
        'float': T.Name('c_float'),
        'double': T.Name('c_double'),
        'int8_t': T.Name('c_int8'),
        'uint8_t': T.Name('c_uint8'),
        'int16_t': T.Name('c_int16'),
        'uint16_t': T.Name('c_uint16'),
        'int32_t': T.Name('c_int32'),
        'uint32_t': T.Name('c_uint32'),
        'int64_t': T.Name('c_int64'),
        'uint64_t': T.Name('c_uint64'),
        'void *': T.Name('c_void_p'),
        'FILE *': T.Name('c_void_p'),
    }


def show_elem(elem: Cursor):
    print(elem.kind)
    for attr_name in dir(elem):
        if attr_name.startswith('__'):
            continue

        try:
            attr = getattr(elem, attr_name)
        except:
            continue

        if callable(attr):
            v = None
            try:
                v = attr()
            except:
                pass
            k = None
            if hasattr(v, 'kind'):
                k = v.kind
            print('   ', attr_name, v, k)
        else:
            print('   ', attr_name, attr)


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
        comment = reformat_comment(elem.raw_comment)
    return comment


def is_valid(name):
    # flag something like below as invalid
    # union SDL_GameControllerButtonBind::(anonymous at /usr/include/SDL2/SDL_gamecontroller.h:75:5)
    return not all(c in name for c in (':', '(', '.', ' '))


class CodeGenerator:
    pass


def parse_sdl_name(name):
    """Parse SDL naming convention and explode it by components

    Examples
    --------
    >>> parse_sdl_name('SDL_GetIndex')
    ('SDL', ['get', 'index'])
    """
    # <module>_CamelCase
    module, name = name.split('_', maxsplit=1)

    names = []
    buffer = ''
    c: str

    for c in name:
        if c == '_':
            continue

        if c.isupper():
            if buffer:
                if buffer + c == 'GL':
                    buffer = ''
                    names.append('GL')
                    continue

                names.append(buffer.lower())
                buffer = ''

            buffer += c
        else:
            buffer += c
    else:
        if buffer:
            names.append(buffer.lower())

    return module, names


class APIGenerator:
    def __init__(self):
        self.type_registry = dict()
        self.new_names = dict()
        self.modules = dict()
        self.module = None
        self.parse_name = parse_sdl_name
        self.topyfunname = lambda names: '_'.join(names)
        self.topyclassname = lambda names: ''.join([n.capitalize() for n in names])

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

        rtype = self.generate_type(definition.result_type)
        args = definition.get_arguments()

        pyargs = []
        cargs = []
        for a in args:
            atype = self.generate_type(a.type)
            aname = a.displayname
            pyargs.append(T.Arg(arg=aname, annotation=T.Name(atype)))
            cargs.append(T.Name(aname))

        c_function = definition.spelling
        module, names = self.parse_name(c_function)

        fundef = T.FunctionDef(self.topyfunname(names), T.Arguments(args=pyargs))
        fundef.body = [
            # T.Expr(T.Str(get_comment(elem))),
            T.Return(T.Call(T.Name(c_function), cargs))
        ]

        # This could be a method
        if len(pyargs) > 0:
            classdef: T.ClassDef = self.type_registry.get(pyargs[0].annotation)

            if classdef is not None:
                # Remove annotation for `self`
                pyargs[0].arg = 'self'
                pyargs[0].annotation = None
                # replace the object by self.handle
                cargs[0] = T.Attribute(T.Name('self'), 'handle')

                # Generate Accessor properties
                if len(pyargs) == 1 and (names[0] == 'get' or names[1] == 'get'):
                    # @property
                    # def x(self):
                    #     return SDL_GetX(self.handle)
                    offset = 1
                    if names[1] == 'set':
                        offset = 2

                    fundef.name = self.topyfunname(names[offset])
                    fundef.decorator_list.append(T.Name('property'))
                    pass

                if len(pyargs) == 2 and (names[0] == 'set' or names[1] == 'set'):
                    # @x.setter
                    # def x(self, x):
                    #     return SDL_SetX(self.handle, x)
                    offset = 1
                    if names[1] == 'set':
                        offset = 2

                    fundef.name = self.topyfunname(names[offset])
                    fundef.decorator_list.append(T.Attribute(T.Name(fundef.name), 'setter'))
                    pass

                # Standard method
                classdef.body.append(fundef)
                return None

        return fundef

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
        dataclass_type = 'struct'
        if elem.kind == CursorKind.UNION_DECL:
            dataclass_type = 'union'

        # --
        c_name = self.get_name(elem, rename=rename)
        module, names = self.parse_name(c_name)

        pyname = self.topyclassname(names)
        class_def = T.ClassDef(pyname)

        # Insert the def inside the registry so we can insert method to it
        self.type_registry[c_name] = class_def

        ctor = T.FunctionDef('__init__', args=T.Arguments(args=[T.Arg('self'), T.Arg('handle', T.Name(c_name))]))
        ctor.body = [
            T.Assign([T.Attribute(T.Name('self'), 'handle')], T.Name('handle'))
        ]
        class_def.body.append(ctor)

        return class_def

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

    def generate(self, tu):
        elem: Cursor
        for elem in tu.cursor.get_children():
            loc: SourceLocation = elem.location

            self.module = self.modules.get(loc.file.name, T.Module(body=[]))
            self.modules[loc.file.name] = self.module

            if not str(loc.file.name).startswith('/usr/include/SDL2'):
                continue

            if elem.kind == CursorKind.FUNCTION_DECL:
                fun = self.generate_function(elem)
                print(unparse(fun))

            elif elem.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL):
                struct = self.generate_struct_union(elem)
                print(unparse(struct))


            # elif elem.kind == CursorKind.TYPEDEF_DECL:
            #     t1 = elem.type
            #     t2 = elem.underlying_typedef_type
            #
            #     # SDL_version = struct SDL_version
            #     if t1.spelling == t2.spelling.split(' ')[-1]:
            #         self.type_registry[t2.spelling] = t1.spelling
            #         continue
            #
            #     t2type = self.generate_type(t2)
            #     self.type_registry[t2type] = t1.spelling
            #     print(f'# typedef\n{t1.spelling} = {t2type}')
            #
            # elif elem.kind == CursorKind.ENUM_DECL:
            #     enum = self.generate_enum(elem)
            #     print(enum)
            #
            # # Global variables
            # elif elem.kind == CursorKind.VAR_DECL:
            #     print(f'{elem.spelling}: {self.generate_type(elem.type)}')
            # else:
            #     show_elem(elem)


if __name__ == '__main__':

    # print(parse_sdl_name('SDL_GetIndex'))
    #
    index = clang.cindex.Index.create()
    tu = index.parse('/usr/include/SDL2/SDL.h')

    gen = APIGenerator()
    gen.generate(tu)


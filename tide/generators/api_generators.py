import clang.cindex
from clang.cindex import Cursor, CursorKind, Type, SourceLocation, TypeKind, TranslationUnit

import tide.generators.nodes as T
from tide.utils.trie import Trie

from astunparse import unparse

import logging

log = logging.getLogger('TIDE')


acronyms_db = Trie()
acronyms_db.insert('GL')
# Run Length Encoding
acronyms_db.insert('RLE')

POD = {
    'int'
    ,'unsigned int'
    ,'long'
    ,'unsigned long'
    ,'unsigned char'
    ,'unsigned short'
    ,'short'
    ,'float'
    ,'double'
    ,'int8_t'
    ,'uint8_t'
    ,'int16_t'
    ,'uint16_t'
    ,'int32_t'
    ,'uint32_t'
    ,'int64_t'
    ,'uint64_t'
}


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

    >>> parse_sdl_name('SDL_GetIndexRLE')
    ('SDL', ['get', 'index', 'RLE'])
    """
    # <module>_CamelCase
    try:
        module, name = name.split('_', maxsplit=1)
    except ValueError:
        return ' ', [name]

    # global acronyms_db
    # acronyms = acronyms_db

    all_upper = False
    names = []
    buffer = ''
    c: str

    for i, c in enumerate(name):
        if c == '_':
            continue

        if c.isupper():
            if buffer and not all_upper:
                names.append(buffer.lower())
                buffer = ''
                all_upper = True

            buffer += c
        else:
            buffer += c
            all_upper = False
    else:
        if buffer:
            if not all_upper:
                buffer = buffer.lower()

            names.append(buffer)

    return module, names


def is_ref(type):
    if isinstance(type, str) and type.startswith('Ref['):
        return True

    if isinstance(type, T.Name):
        return is_ref(type.id)

    # Handle the AST version
    return False


class Callable:
    def __init__(self, args, returntype):
        self.args = args
        self.returntype = returntype


    def __str__(self):
        args = ', '.join(self.args)
        return f'Callable[[{args}], {self.returntype}]'

    def __hash__(self):
        return hash(str(self))


class Ref:
    def __init__(self, base):
        self.base = base
    
    def __str__(self):
        return f'Ref[{self.base}]'

    def __hash__(self):
        return hash(str(self))


class Const:
    def __init__(self, base):
        self.base = base
    
    def __str__(self):
        return f'Const[{self.base}]'

    def __hash__(self):
        return hash(str(self))


def get_base_type(type):
    if isinstance(type, (Ref, Const)):
        return type.base
    return str(type)


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

    def get_typename(self, type):
        typedef = self.generate_type(type)

        if isinstance(typedef, (str, Const, Ref, Callable)):
            return str(typedef)

        if isinstance(typedef, T.ClassDef):
            return typedef.name

        return typedef 

    def _generate_type(self, type: Type, depth=0):
        if type.kind == TypeKind.VOID:
            return 'None'

        if type.kind == TypeKind.POINTER and type.get_pointee().kind == TypeKind.VOID:
            return 'any'

        if type.kind == TypeKind.ELABORATED or type.kind == TypeKind.RECORD:
            return type.spelling.replace('struct', '').strip()

        if type.kind == TypeKind.POINTER:
            pointee: Type = type.get_pointee()

            if pointee.kind is TypeKind.TYPEDEF:
                return Ref(pointee.spelling)

            # in python every object is a pointer
            if pointee.kind in (TypeKind.RECORD, TypeKind.FUNCTIONPROTO, TypeKind.UNEXPOSED):
                return self._generate_type(pointee, depth + 1)

            if not pointee.is_pod():
                show_elem(pointee)

            # for native types we need to keep ref because python will copy them
            return Ref(self._generate_type(pointee, depth + 1))

        if type.kind == TypeKind.CHAR_S:
            return 'str'

        if type.is_const_qualified():
            typename = type.spelling.replace('const ', '')
            return Const(typename)

        if type.kind == TypeKind.TYPEDEF:
            return type.spelling

        if type.kind == TypeKind.FUNCTIONPROTO or (type.kind == TypeKind.UNEXPOSED and type.get_canonical().kind == TypeKind.FUNCTIONPROTO):
            canon = type.get_canonical()
            rtype = canon.get_result()

            args = []
            for arg in canon.argument_types():
                args.append(self._generate_type(arg, depth + 1))

            return Callable(args, self._generate_type(rtype, depth + 1))

        # show_elem(type)
        return type.spelling

    def generate_function(self, elem: Cursor):
        """Generate the Python function corresponding to the c function

        Examples
        --------
        >>> tu, index = parse_clang('double add(double a, double b);')
        >>> modules = APIGenerator().generate(tu)
        >>> for k, m in modules.items():
        ...     print(f'# {k}')
        ...     print(unparse(m))
        # string.c
        <BLANKLINE>
        <BLANKLINE>
        <BLANKLINE>
        def add(a: double, b: double) -> double:
            return add(a, b)
        <BLANKLINE>
        """
        definition: Cursor = elem.get_definition()

        if definition is None:
            definition = elem

        log.debug(f'Generate function {definition.spelling}')
        rtype = self.get_typename(definition.result_type)
        args = definition.get_arguments()

        pyargs = []
        cargs = []
        for a in args:
            atype = self.get_typename(a.type)
            aname = a.displayname
            pyargs.append(T.Arg(arg=aname, annotation=T.Name(atype)))
            cargs.append(T.Name(aname))

        c_function = definition.spelling
        module, names = self.parse_name(c_function)

        fundef = T.FunctionDef(self.topyfunname(names), T.Arguments(args=pyargs))
        fundef.returns = T.Name(rtype)
        fundef.body = [
            # this is docstring but it is not unparsed correctly
            # T.Expr(T.Str(get_comment(elem))),
            T.Return(T.Call(T.Name(c_function), cargs))
        ]

        # This could be a method
        if len(pyargs) > 0:
            # log.debug(f'Looking for {pyargs[0].annotation} in {self.type_registry}')

            selftype = pyargs[0].annotation
            classdef = None

            # For class grouping the first arg needs to be a reference to the class type
            lookuptype = selftype.id
            if isinstance(lookuptype, Ref):
                lookuptype = lookuptype.base
                classdef: T.ClassDef = self.type_registry.get(lookuptype)

                if isinstance(classdef, T.ClassDef):
                    log.debug(f'found {classdef} for {lookuptype}')
                else:
                    classdef = None

            if classdef is not None:
                # Remove annotation for `self`
                pyargs[0].arg = 'self'
                pyargs[0].annotation = None
                # replace the object by self.handle
                cargs[0] = T.Attribute(T.Name('self'), 'handle')

                # Generate Accessor properties
                if len(pyargs) == 1 and names[0] == 'get':
                    # @property
                    # def x(self):
                    #     return SDL_GetX(self.handle)
                    offset = 1
                    if names[1] == 'set':
                        offset = 2

                    fundef.name = self.topyfunname(names[offset:])
                    fundef.decorator_list.append(T.Name('property'))

                if len(pyargs) == 2 and (names[0] == 'get' or names[1] == 'get') and is_ref(pyargs[1].annotation):
                    rtype = pyargs[1].annotation
                    cargs[1] = T.Name('result')

                    offset = 1
                    if names[1] == 'get':
                        offset = 2

                    fundef.name = self.topyfunname(names[offset:])
                    fundef.decorator_list.append(T.Name('property'))
                    fundef.returns = rtype

                    fundef.args.args = [fundef.args.args[0]]
                    fundef.body = [
                        # T.Expr(T.Str(get_comment(elem))),
                        T.Assign([T.Name('result')], T.Call(rtype)),
                        T.Expr(T.Call(T.Name(c_function), cargs)),
                        # T.Assign([T.Name('err')], T.Call(T.Name(c_function), cargs)),
                        # T.If(T.Name('err'), T.Return(T.Name('None'))),
                        T.Return(T.Name('result'))
                    ]

                if len(pyargs) == 2 and (names[0] == 'set' or names[1] == 'set'):
                    # @x.setter
                    # def x(self, x):
                    #     return SDL_SetX(self.handle, x)
                    offset = 1
                    if names[1] == 'set':
                        offset = 2

                    fundef.name = self.topyfunname(names[offset:])
                    fundef.decorator_list.append(T.Attribute(T.Name(fundef.name), 'setter'))

                # Standard method
                log.debug(f'Adding method to {classdef.name}')
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

            #if not str(loc.file.name).startswith('/usr/include/SDL2'):
            #    continue
            
            expr = None
            if elem.kind == CursorKind.FUNCTION_DECL:
                expr = self.generate_function(elem)

            elif elem.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL):
                expr = self.generate_struct_union(elem)

            elif elem.kind == CursorKind.TYPEDEF_DECL:
                t1 = elem.type
                t2 = elem.underlying_typedef_type

                classdef = self.type_registry.get(t2.spelling)

                if classdef is not None:
                    log.debug(f'{t1.spelling} = {classdef}')
                    self.type_registry[t1.spelling] = classdef
                else:
                    log.debug(f'typdef {t1.spelling} = {t2.spelling}')

            if expr is not None:
                self.module.body.append(T.Expr(expr))

        return self.modules

                # # SDL_version = struct SDL_version
                # if t1.spelling == t2.spelling.split(' ')[-1]:
                #     self.type_registry[t2.spelling] = t1.spelling
                #     continue

                # t2type = self.generate_type(t2)
                # self.type_registry[t2type] = t1.spelling
                # print(f'# typedef\n{t1.spelling} = {t2type}')
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


def parse_clang(code, ext='c', source='string') -> TranslationUnit:
    """Parse C code using clang, returns a translation unit

    Examples
    --------

    >>> tu, index = parse_clang('double add(double a, double b){ return a + b; }')
    >>> for elem in tu.cursor.get_children():
    ...     print(elem.spelling, elem.kind)
    add CursorKind.FUNCTION_DECL
    """
    fname = f'{source}.{ext}'
    index = clang.cindex.Index.create()
    tu = index.parse(path=fname, unsaved_files=[(fname, code)])
    return tu, index


def parse_function(fun):
    pass


if __name__ == '__main__':
    import sys
    logging.basicConfig(stream=sys.stdout)
    log.setLevel(logging.DEBUG)

    # print(parse_sdl_name('SDL_GetIndex'))
    #
    index = clang.cindex.Index.create()

    file = '/usr/include/SDL2/SDL.h'
    # file = '/home/setepenre/work/tide/tests/binding/typedef_func.h'
    # file = '/home/setepenre/work/tide/tests/binding/method_transformer.h'
    tu = index.parse(file)

    gen = APIGenerator()
    modules = gen.generate(tu)

    for k, m in modules.items():
        print(f'# {k}')
        print(unparse(m))

    # for k, v in gen.type_registry.items():
    #    print(k, '=>', v)


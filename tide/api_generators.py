import clang.cindex
from clang.cindex import Cursor, CursorKind, Type, SourceLocation, TypeKind

index = clang.cindex.Index.create()
tu = index.parse('/usr/include/SDL2/SDL.h')

elem: Cursor
decl = {
    # CursorKind.STRUCT_DECL,
    # CursorKind.TYPEDEF_DECL,
    CursorKind.FUNCTION_DECL
}


def generate_type(type: Type):
    if type.kind == TypeKind.VOID:
        return 'None'

    if type.kind == TypeKind.POINTER and type.get_pointee().kind == TypeKind.VOID:
        return 'any'

    if type.kind == TypeKind.POINTER:
        pointee = type.get_pointee()

        # in python every object is a pointer
        if pointee.kind in (TypeKind.RECORD, TypeKind.FUNCTIONPROTO, TypeKind.UNEXPOSED):
            return generate_type(pointee)

        # for native types we need to keep ref because python will copy them
        return f'Ref[{generate_type(pointee)}]'

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
            args.append(generate_type(arg))

        args = ', '.join(args)
        # show_elem(type.get_canonical())
        return f'Callable[[{args}], {generate_type(rtype)}]'

    # show_elem(type)
    return type.spelling


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


def generate_function(elem: Cursor):
    definition: Cursor = elem.get_definition()

    if definition is None:
        definition = elem

    pyargs = []

    rtype = generate_type(definition.result_type)
    args = definition.get_arguments()

    for a in args:
        atype = generate_type(a.type)
        aname = a.displayname
        pyargs.append(f'{aname}: {atype}')

    funnane = definition.spelling
    pyargs = ', '.join(pyargs)

    comment = get_comment(elem)
    return f'\ndef {funnane}({pyargs}) -> {rtype}:\n{comment}    pass\n'


def is_valid(name):
    # flag something like below as invalid
    # union SDL_GameControllerButtonBind::(anonymous at /usr/include/SDL2/SDL_gamecontroller.h:75:5)
    return not all(c in name for c in (':', '(', '.', ' '))


def get_name(elem, rename=None):
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


def get_comment(elem, indent='    '):
    comment = ''
    if elem.brief_comment:
        comment = f'{indent}"""{elem.brief_comment}"""\n'
    return comment


def find_anonymous_fields(elem):
    # Find Anonymous struct or union
    # to rename them so something valid
    anonymous = dict()
    anonymous_renamed = dict()

    for attr in elem.get_children():
        if attr.kind == CursorKind.UNION_DECL or attr.kind == CursorKind.STRUCT_DECL:
            attr_type_name = get_name(attr)
            if not attr_type_name:
                anonymous[attr.get_usr()] = attr

        if attr.kind == CursorKind.FIELD_DECL:
            usr = attr.type.get_declaration().get_usr()
            if usr in anonymous:
                anonymous_renamed[usr] = '_' + get_name(attr).capitalize()

    return anonymous_renamed


def generate_struct_union(elem: Cursor, depth=1, nested=False, rename=None):
    pyname = get_name(elem, rename=rename)

    base = '    ' * (depth - 1)
    indent = '    ' * depth

    dataclass_type = 'struct'
    if elem.kind == CursorKind.UNION_DECL:
        dataclass_type = 'union'

    anonymous_renamed = find_anonymous_fields(elem)

    attrs = []
    attr: Cursor
    for attr in elem.get_children():
        if attr.kind == CursorKind.FIELD_DECL:
            # Rename anonymous types
            uid = attr.type.get_declaration().get_usr()

            if uid in anonymous_renamed:
                typename = anonymous_renamed[uid]
            else:
                typename = generate_type(attr.type)

            attrs.append(f'{attr.spelling}: {typename}')

        elif attr.kind in (CursorKind.UNION_DECL, CursorKind.STRUCT_DECL):
            attrs.append(generate_struct_union(attr, depth + 1, nested=True, rename=anonymous_renamed))
        else:
            print('NESTED ', attr.kind)

    attrs = f'\n{indent}'.join(attrs)
    if not attrs:
        attrs = 'pass'

    comment = get_comment(elem, indent)
    return f'\n{base}@{dataclass_type}\n{base}class {pyname}:\n{comment}{indent}{attrs}\n'


def generate_enum(elem: Cursor):
    name = get_name(elem)

    values = []
    for value in elem.get_children():
        if value.kind == CursorKind.ENUM_CONSTANT_DECL:
            values.append(f'{get_name(value)} = {value.enum_value}')
        else:
            print('ERROR')
            show_elem(value)

    values = '\n'.join(values)
    return f"\nclass {name}(enum):\n    pass\n\n{values}\n"


for elem in tu.cursor.get_children():
    loc: SourceLocation = elem.location

    if not str(loc.file.name).startswith('/usr/include/SDL2'):
        continue

    # print(f'# {loc.file.name}')

    if elem.kind == CursorKind.FUNCTION_DECL:
        fun = generate_function(elem)
        print(fun)

    elif elem.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL):
        struct = generate_struct_union(elem)
        print(struct)

    elif elem.kind == CursorKind.TYPEDEF_DECL:
        t1 = elem.type
        t2 = elem.underlying_typedef_type

        # SDL_version = struct SDL_version
        if t1.spelling == t2.spelling.split(' ')[-1]:
            continue

        print(f'{t1.spelling} = {generate_type(t2)}')
    elif elem.kind == CursorKind.ENUM_DECL:
        enum = generate_enum(elem)
        print(enum)

    # Global variables
    elif elem.kind == CursorKind.VAR_DECL:
        print(f'{elem.spelling}: {generate_type(elem.type)}')
    else:
        show_elem(elem)


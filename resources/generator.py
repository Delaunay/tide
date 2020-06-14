"""Generate python AST nodes given the ASDL file"""

import os
import resources.asdl as asdl


TYPES = {
    'mod': 'Module',
    'stmt': 'Statement',
    'expr': 'Expression',
    'identifier': 'Identifier',
    'unaryop': 'UnaryOp',
    'operator': 'Operator',
    'boolop': 'BoolOp',
    'slice': 'Slice',
    'expr_context': 'ExpressionContext',
    'string': 'str',
    'int': 'int',
    'cmpop': 'Compare',
    'type_ignores': 'any'
}


def get_type(type):
    return TYPES.get(type, '')


def get_parent(type):
    t = get_type(type)
    if t:
        return f'({t})'
    return ''


def generate_field(field: asdl.Field):
    type = get_type(field.type)

    if field.seq and type != '':
        type = f'List[{type}]'

    if field.opt and type != '':
        type = f'Optional[{type}]'

    if type != '':
        return f'{field.name}: {type}'

    return f'{field.name} = None'


def generate_struct(name, fields, type, attributes):
    parent = get_parent(type)

    if not fields and not attributes:
        fields = 'pass'
    else:
        fields = [generate_field(f) for f in fields]
        fields = '\n    '.join(fields)

    attr = ''
    if attributes:
        attr = [generate_field(attr) for attr in attributes]
        attr = '\n    ' + '\n    '.join(attr)

    code = f"""@dataclass
    |class {name}{parent}:
    |    {fields}{attr}
    """.replace('    |', '')

    print(code)



def generate_product(type, prod, attributes):
    print('# ', type, prod)

    if isinstance(prod, asdl.Constructor):
        generate_struct(prod.name, prod.fields, type, attributes)
    elif isinstance(prod, asdl.Product):
        generate_struct(get_type(type), prod.fields, '', attributes)


def generate_ast_nodes():
    asdl_file = os.path.join(os.path.dirname(__file__), 'python.asdl')

    with open(asdl_file, 'r') as f:
        asdl_buffer = f.read()

    parser = asdl.ASDLParser()
    module = parser.parse(asdl_buffer)

    # insert AST node types
    for k, v in module.types.items():
        if isinstance(v, asdl.Product):
            nk = k.capitalize()
            TYPES[k] = nk

    # Generate the Nodes
    for k, v in module.types.items():
        if isinstance(v, asdl.Product):
            generate_product(k, v, v.attributes)

        if isinstance(v, asdl.Sum):
            for type in v.types:
                generate_product(k, type, v.attributes)


generate_ast_nodes()

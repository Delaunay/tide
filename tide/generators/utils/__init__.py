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

operators = {
    'is': '==',
    'lt': '<',
    'gt': '>',
    'lte': '<=',
    'gte': '>=',
    'noteq': '!=',
    'eq': '==',
    'mul': '*',
    'add': '+',
    'sub': '-',
    'pow': None,
}

booloperator = {
    'and': '&&',
    'or': '||',
}

libreplace = {
    'math': ('cmath', 'system'),
    'typing': ('', 'ignore'),
    'tide.runtime.kiwi': ('', 'ignore')
}

builtintypes = {
    'int': int,
    'str': str,
    'float': float,
    'Tuple': type,
    'bool': bool,
}

typing_types = {
    'List', 'Tuple', 'Dict', 'Set'
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

        return [self.project_name] + filename.replace('.py', '').split('/'), True

    def module(self, module_path, level=0):
        print(f'Looking up {module_path}')
        libname, libspace = libreplace.get(module_path, (None, None))

        if libname is None:
            name = module_path.replace('.', '/') + '.h'
            return f'"{name}"'

        if libname == '' and libspace == 'ignore':
            return ''

        if libspace == 'system':
            return f'<{libname}>'

        return f'"{libname}"'

    def header_guard(self, filename):
        if not filename.startswith(self.root):
            return (self.project_name + '_' +
                    filename.replace('/', '_').replace('.py', '')
                    + '_HEADER').upper()

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


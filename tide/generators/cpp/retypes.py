

class KiwiType:
    pass


class MetaType(KiwiType):
    global_count = 0

    def __init__(self):
        self.id = self.global_count
        MetaType.global_count += 1
        self.clues = []

    def __repr__(self):
        clue = None
        if len(self.clues) > 0:
            clue = self.clues[-1]

        return f'MetaType<{self.id}>({clue})'

    def add_clue(self, clue):
        if isinstance(clue, NoneType):
            return

        self.clues.append(clue)

    def infer(self):
        if len(self.clues) == 1:
            return self.clues[0]

        if len(self.clues) == 0:
            return NoneType

        return self.clues[-1]


class NoneType(KiwiType):
    pass


class TypeType(KiwiType):
    pass


class StructType(KiwiType):
    def __init__(self, types):
        self.types = types


class UnionType(KiwiType):
    def __init__(self, types):
        self.types = types


class Callable(KiwiType):
    def __init__(self, args, return_type):
        self.args = args
        self.return_type = return_type


class Generic(KiwiType):
    def __init__(self, typename, *types):
        self.typename = typename
        self.types = types


class TypeRef(KiwiType):
    def __init__(self, name):
        self.name = name

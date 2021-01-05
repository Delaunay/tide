# Builtin file parse to populate base typing context for type inference

class float:
    def __add__(self, other: 'float') -> 'float':
        raise NotImplemented

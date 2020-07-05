from ast import AST, iter_fields

from tide.log import debug


class NodeVisitor:
    """Rip off of ast.NodeVisitor but allows for arbitrary arguments"""
    def visit(self, node, *args, depth=-1, **kwargs):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, *args, depth=depth + 1, **kwargs)

    def base_visit(self, node, *args, depth=0, **kwargs):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        self.visit(item, *args, depth=depth, **kwargs)

            elif isinstance(value, AST):
                self.visit(value, *args, depth=depth, **kwargs)

    def generic_visit(self, node, *args, depth=0, **kwargs):
        def sep(i):
            if i % 2 == 0:
                return '|'
            else:
                return ':'

        offset = ''.join([sep(i) for i in range(depth)])
        debug(f'{offset}+-> {type(node).__name__}')
        r = self.base_visit(node)
        debug(f'{offset}+-< {type(node).__name__}')
        return r

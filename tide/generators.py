import ast
from tide.nodes import *


class GenerateCpp(ast.NodeVisitor):

    def visit_arg(self, args):
        print(args)
        self.generic_visit(args)

    def visit_BinOp(self, args):
        print(args)
        self.generic_visit(args)

    def visit_arguments(self, args):
        print(args)
        self.generic_visit(args)

    def visit_Statement(self, stmt):
        print(stmt)
        self.generic_visit(stmt)

    def visit_Expression(self, expr):
        print(expr)
        self.generic_visit(expr)

    def visit_Load(self, expr: Load):
        self.generic_visit(expr)
        
    def generic_visit(self, node):
        print(type(node))
        super(GenerateCpp, self).generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        self.generic_visit(node)


data = ast.parse("""
def add(a: int, b: int = 0, *arg, a=1, **kwargs) -> int:
    return a + b
""")


print(data)

visitor = GenerateCpp()
visitor.visit(data)




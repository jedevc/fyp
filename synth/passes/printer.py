import sys

from ..parser import (
    Visitor,
    ChunkNode,
    TypeNode,
    VariableNode,
    SpecialVariableNode,
    SpecNode,
)


class PrinterVisitor(Visitor):
    def __init__(self, output=sys.stdout):
        super().__init__()
        self.output = output

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)

    def visit_chunk(self, node: ChunkNode):
        self._print("chunk ")
        for i, var in enumerate(node.variables):
            var.accept(self)
            if i == len(node.variables) - 1:
                self._println()
            else:
                self._println(",")
                self._print("      ")

    def visit_variable(self, node: VariableNode):
        self._print(f"{node.name} : ")
        node.vartype.accept(self)

    def visit_special_variable(self, node: SpecialVariableNode):
        self._print(f"${node.name}")

    def visit_type(self, node: TypeNode):
        self._print(node.base)
        if node.size > 1:
            self._print(f"[{node.size}]")

    def _print(self, msg=""):
        print(msg, end="", file=self.output)

    def _println(self, msg=""):
        print(msg, file=self.output)

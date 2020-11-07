import sys

from ..parser import (
    SpecNode,
    BlockNode,
    CallNode,
    AssignmentNode,
    FunctionNode,
    VariableNode,
    ChunkNode,
    TypeNode,
    DeclarationNode,
    SpecialDeclarationNode,
    Visitor,
)


class PrinterVisitor(Visitor):
    def __init__(self, output=sys.stdout):
        super().__init__()
        self.output = output

        self.indent = 0

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)
        self._println()
        for block in node.blocks:
            block.accept(self)

    def visit_chunk(self, node: ChunkNode):
        self._print("chunk ")
        self.indent += 6
        for i, var in enumerate(node.variables):
            var.accept(self)
            if i == len(node.variables) - 1:
                self._println()
            else:
                self._println(",")
        self.indent -= 6

    def visit_declaration(self, node: DeclarationNode):
        self._print(f"{node.name} : ")
        node.vartype.accept(self)

    def visit_special_declaration(self, node: SpecialDeclarationNode):
        self._print(f"${node.name}")

    def visit_type(self, node: TypeNode):
        self._print(node.base)
        if node.size > 1:
            self._print(f"[{node.size}]")

    def visit_block(self, node: BlockNode):
        self._print("block ")
        self._print(node.label)
        self.indent += 4
        self._println(" {")
        for i, statement in enumerate(node.statements):
            statement.accept(self)
            if i != len(node.statements) - 1:
                self._println()
        self.indent -= 4
        self._println()
        self._println("}")

    def visit_assignment(self, node: AssignmentNode):
        self._print(node.name)
        self._print(" = ")
        node.expression.accept(self)

    def visit_call(self, node: CallNode):
        self._print("call ")
        self._print(node.target)

    def visit_variable(self, node: VariableNode):
        if node.address:
            self._print("&")
        self._print(node.target)

    def visit_function(self, node: FunctionNode):
        self._print(node.name)
        self._print("(")
        for i, arg in enumerate(node.arguments):
            arg.accept(self)
            if i != len(node.arguments) - 1:
                self._print(", ")
        self._print(")")

    def _print(self, msg=""):
        print(msg, end="", file=self.output)

    def _println(self, msg=""):
        print(msg, file=self.output)
        if self.indent > 0:
            print(self.indent * " ", file=self.output, end="")
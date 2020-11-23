import sys
from typing import List, Union

from ..parser import (
    AssignmentNode,
    BlockNode,
    CallNode,
    ChunkNode,
    DeclarationNode,
    ExternChunkNode,
    FunctionNode,
    SpecialDeclarationNode,
    SpecNode,
    TypeNode,
    ValueNode,
    VariableNode,
    Visitor,
)


class PrinterVisitor(Visitor):
    """
    A pretty-printer for the AST, used to generate an equivalent
    representation of the source code.

    This visitor should preserve the property:
        parse(print(parse(x))) = parse(x)

    This is mostly used for debugging, and to gain insight into how the lexer
    and parser are interpreting the provided code.
    """

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
        self._visit_vars("chunk", node.variables)

    def visit_extern(self, node: ExternChunkNode):
        self._visit_vars("extern", node.variables)

    def _visit_vars(
        self, name: str, variables: List[Union[DeclarationNode, SpecialDeclarationNode]]
    ):
        self._print(name + " ")
        self.indent += len(name) + 1
        for i, var in enumerate(variables):
            var.accept(self)
            if i != len(variables) - 1:
                self._println(",")
        self.indent -= len(name) + 1
        self._println()

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
        self._print(node.name)
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
        self._print(node.target)
        self._print(" = ")
        node.expression.accept(self)

    def visit_call(self, node: CallNode):
        self._print("call ")
        self._print(node.target)

    def visit_variable(self, node: VariableNode):
        if node.address:
            self._print("&")
        self._print(node.name)

    def visit_function(self, node: FunctionNode):
        self._print(node.target)
        self._print("(")
        for i, arg in enumerate(node.arguments):
            arg.accept(self)
            if i != len(node.arguments) - 1:
                self._print(", ")
        self._print(")")

    def visit_value(self, node: ValueNode):
        val = str(node.value)
        if node.is_str():
            self._print(quote(val))
        elif node.is_int():
            self._print(val)
        else:
            raise RuntimeError()

    def _print(self, msg: str = ""):
        print(msg, end="", file=self.output)

    def _println(self, msg: str = ""):
        print(msg, file=self.output)
        if self.indent > 0:
            print(self.indent * " ", file=self.output, end="")


def quote(s: str) -> str:
    if '"' not in s:
        return '"' + s + '"'
    elif "'" not in s:
        return "'" + s + "'"
    else:
        # shouldn't be possible?
        return "`" + s + "`"

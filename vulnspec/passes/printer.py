import sys
from typing import List, TextIO

from ..node import (
    ArrayNode,
    ArrayTypeNode,
    AssignmentNode,
    BinaryOperationNode,
    BlockNode,
    BoolValueNode,
    CallNode,
    CastNode,
    ChunkNode,
    DeclarationNode,
    DerefNode,
    ExpressionStatementNode,
    ExternChunkNode,
    FloatValueNode,
    FunctionNode,
    FuncTypeNode,
    IfNode,
    IntValueNode,
    LiteralExpressionNode,
    LiteralStatementNode,
    PointerTypeNode,
    RefNode,
    SimpleTypeNode,
    SizeOfNode,
    SpecNode,
    SplitNode,
    StatementNode,
    StringValueNode,
    TemplateValueNode,
    UnaryOperationNode,
    ValueNode,
    VariableNode,
    Visitor,
    WhileNode,
)


class PrinterVisitor(Visitor[None]):
    """
    A pretty-printer for the AST, used to generate an equivalent
    representation of the source code.

    This visitor should preserve the property:
        parse(print(parse(x))) = parse(x)

    This is mostly used for debugging, and to gain insight into how the lexer
    and parser are interpreting the provided code.
    """

    def __init__(self, output: TextIO = sys.stdout):
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
        self._visit_vars("chunk", node.variables, node.constraints)

    def visit_extern(self, node: ExternChunkNode):
        self._visit_vars("extern", node.variables, node.constraints)

    def _visit_vars(
        self, name: str, variables: List[DeclarationNode], constraints: List[str]
    ):
        self._print(f"{name} ")
        if constraints:
            self._print(f"({', '.join(constraints)}) ")

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
        if node.initial:
            self._print(" = ")
            node.initial.accept(self)

    def visit_type_simple(self, node: SimpleTypeNode):
        self._print(node.core)

    def visit_type_pointer(self, node: PointerTypeNode):
        self._print("*")
        node.base.accept(self)

    def visit_type_array(self, node: ArrayTypeNode):
        self._print(f"[{node.size}]")
        node.base.accept(self)

    def visit_type_func(self, node: FuncTypeNode):
        self._print("fn (")
        for i, arg in enumerate(node.args):
            arg.accept(self)
            if i != len(node.args) - 1:
                self._print(", ")
        self._print(") ")
        node.ret.accept(self)

    def visit_block(self, node: BlockNode):
        self._print("block ")
        if node.constraints:
            self._print(f"({', '.join(node.constraints)}) ")
        self._print(node.name)
        self._visit_scope(node.statements)
        self._println()

    def visit_assignment(self, node: AssignmentNode):
        node.target.accept(self)
        self._print(" = ")
        node.expression.accept(self)

    def visit_split(self, node: SplitNode):
        self._print("...")

    def visit_call(self, node: CallNode):
        self._print("call ")
        self._print(node.target)

    def visit_cast(self, node: CastNode):
        node.expr.accept(self)
        self._print(" as (")
        node.cast.accept(self)
        self._print(")")

    def visit_literal_expr(self, node: LiteralExpressionNode):
        self._print(f"$({node.content.strip()})")

    def visit_literal_stmt(self, node: LiteralStatementNode):
        self._print(f"$({node.content.strip()})")

    def visit_variable(self, node: VariableNode):
        self._print(node.name)

    def visit_ref(self, node: RefNode):
        self._print("&")
        node.target.accept(self)

    def visit_deref(self, node: DerefNode):
        self._print("*(")
        node.target.accept(self)
        self._print(")")

    def visit_array(self, node: ArrayNode):
        node.target.accept(self)
        self._print("[")
        node.index.accept(self)
        self._print("]")

    def visit_function(self, node: FunctionNode):
        if isinstance(node.target, VariableNode):
            self._print(node.target.name)
        else:
            self._print("(")
            node.target.accept(self)
            self._print(")")

        self._print("(")
        for i, arg in enumerate(node.arguments):
            arg.accept(self)
            if i != len(node.arguments) - 1:
                self._print(", ")
        self._print(")")

    def visit_value(self, node: ValueNode):
        if isinstance(node, StringValueNode):
            self._print(repr(node.value))
        elif isinstance(node, IntValueNode):
            self._print(str(node.value))
        elif isinstance(node, FloatValueNode):
            self._print(f"{node.left}.{node.right}")
        elif isinstance(node, BoolValueNode):
            if node.value:
                self._print("true")
            else:
                self._print("false")
        elif isinstance(node, TemplateValueNode):
            self._print(f"<{node.name}; {node.definition}>")
        else:
            print(node)
            raise RuntimeError()

    def visit_sizeof(self, node: SizeOfNode):
        self._print(f"sizeof({node.tp.accept(self)})")

    def visit_unary(self, node: UnaryOperationNode):
        self._print("(")
        self._print(node.op.opstr())
        node.item.accept(self)
        self._print(")")

    def visit_binary(self, node: BinaryOperationNode):
        self._print("(")
        node.left.accept(self)
        self._print(f" {node.op.opstr()} ")
        node.right.accept(self)
        self._print(")")

    def visit_if(self, node: IfNode):
        self._print("if ")
        node.condition.accept(self)
        self._visit_scope(node.statements)

        if node.else_if:
            self._print(" else ")
            node.else_if.accept(self)
        if node.else_statements:
            self._print(" else ")
            self._visit_scope(node.else_statements)

    def visit_while(self, node: WhileNode):
        self._print("while ")
        node.condition.accept(self)
        self._visit_scope(node.statements)

    def visit_exprstmt(self, node: ExpressionStatementNode):
        node.expression.accept(self)

    def _visit_scope(self, stmts: List[StatementNode]):
        self.indent += 4
        self._println(" {")
        for i, statement in enumerate(stmts):
            statement.accept(self)
            if i != len(stmts) - 1:
                self._println()
        self.indent -= 4
        self._println()
        self._print("}")

    def _print(self, msg: str = ""):
        print(msg, end="", file=self.output)

    def _println(self, msg: str = ""):
        print(msg, file=self.output)
        if self.indent > 0:
            print(self.indent * " ", file=self.output, end="")

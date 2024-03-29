import json
import sys
from typing import Collection, Optional, TextIO, Union

from ..graph import ChunkVariable
from ..node import (
    ArrayNode,
    ArrayTypeNode,
    AssignmentNode,
    BinaryOperationNode,
    BlockNode,
    CallNode,
    CastNode,
    ChunkNode,
    DeclarationNode,
    DerefNode,
    ExpressionStatementNode,
    ExternChunkNode,
    FunctionNode,
    FuncTypeNode,
    IfNode,
    LiteralExpressionNode,
    LiteralStatementNode,
    Node,
    PointerTypeNode,
    RefNode,
    SimpleTypeNode,
    SizeOfExprNode,
    SizeOfTypeNode,
    SpecNode,
    SplitNode,
    UnaryOperationNode,
    ValueNode,
    VariableNode,
    Visitor,
    WhileNode,
)


class VisualizerVisitor(Visitor[int]):
    """
    A visualizer for the AST, used to generate a graphviz diagram that can be
    rendered to make pretty pictures and visualizations of the result of the
    parsing process.

    This can be used for future debugging but will hopefully(!) be used in my
    final report.
    """

    def __init__(self, output: TextIO = sys.stdout):
        super().__init__()
        self.output = output

        self._counter = 0

    def visit_spec(self, node: SpecNode) -> int:
        self._raw("digraph AST {")
        self._command("node [shape=box]")

        root = self._node("spec")

        for chunk in node.chunks:
            child = chunk.accept(self)
            self._line(root, child)
        for block in node.blocks:
            child = block.accept(self)
            self._line(root, child)

        self._raw("}")

        return root

    def visit_chunk(self, node: ChunkNode) -> int:
        return self._connect("chunk", node.variables)

    def visit_extern(self, node: ExternChunkNode) -> int:
        return self._connect("extern", node.variables)

    def visit_declaration(self, node: DeclarationNode) -> int:
        cvar = ChunkVariable(node.name, node.vartype, None)
        root = self._node(f"var {cvar.typename()}")
        if node.initial:
            child = node.initial.accept(self)
            self._line(root, child)

        return root

    def visit_type_simple(self, node: SimpleTypeNode):
        return self._node(ChunkVariable("", node, None).typename())

    def visit_type_pointer(self, node: PointerTypeNode):
        return self._node(ChunkVariable("", node, None).typename())

    def visit_type_array(self, node: ArrayTypeNode):
        return self._node(ChunkVariable("", node, None).typename())

    def visit_type_func(self, node: FuncTypeNode):
        return self._node(ChunkVariable("", node, None).typename())

    def visit_block(self, node: BlockNode) -> int:
        return self._connect(f"block {node.name}", node.statements)

    def visit_assignment(self, node: AssignmentNode) -> int:
        return self._connect("=", (node.target, node.expression))

    def visit_split(self, node: SplitNode) -> int:
        return self._node("...")

    def visit_call(self, node: CallNode) -> int:
        return self._node(f"call {node.target}")

    def visit_cast(self, node: CastNode) -> int:
        cvar = ChunkVariable("", node.cast, None)
        return self._connect(f"cast {cvar.typestr()}", node.expr)

    def visit_variable(self, node: VariableNode) -> int:
        return self._node(f"variable {node.name}")

    def visit_ref(self, node: RefNode) -> int:
        return self._connect("&", node.target)

    def visit_deref(self, node: DerefNode) -> int:
        return self._connect("*", node.target)

    def visit_array(self, node: ArrayNode) -> int:
        return self._connect("[]", (node.target, node.index))

    def visit_function(self, node: FunctionNode) -> int:
        return self._connect("apply", [node.target, *node.arguments])

    def visit_value(self, node: ValueNode) -> int:
        return self._node(str(node))

    def visit_sizeof_expr(self, node: SizeOfExprNode) -> int:
        return self._connect("sizeof", node.target)

    def visit_sizeof_type(self, node: SizeOfTypeNode) -> int:
        return self._connect("sizeof", node.target)

    def visit_unary(self, node: UnaryOperationNode) -> int:
        return self._connect(node.op.opstr(), node.item)

    def visit_binary(self, node: BinaryOperationNode) -> int:
        return self._connect(node.op.opstr(), (node.left, node.right))

    def visit_if(self, node: IfNode) -> int:
        root = self._node("if")
        condition = self._connect("condition", node.condition)
        self._line(root, condition)
        statements = self._connect("then", node.statements)
        self._line(root, statements)

        if node.else_if:
            child = node.else_if.accept(self)
            self._line(root, child)
        if node.else_statements:
            child = self._connect("else", node.else_statements)
            self._line(root, child)

        return root

    def visit_while(self, node: WhileNode) -> int:
        root = self._node("while")
        condition = self._connect("condition", node.condition)
        self._line(root, condition)
        statements = self._connect("condition", node.statements)
        self._line(root, statements)

        return root

    def visit_exprstmt(self, node: ExpressionStatementNode) -> int:
        return node.expression.accept(self)

    def visit_literal_expr(self, node: LiteralExpressionNode) -> int:
        return self._node(f"$({node.content.strip()})")

    def visit_literal_stmt(self, node: LiteralStatementNode) -> int:
        return self._node(f"$({node.content.strip()})")

    def _connect(self, msg: str, children: Union[Node, Collection[Node]]) -> int:
        root = self._node(msg)
        if isinstance(children, Node):
            children = [children]

        for i, child in enumerate(children):
            if i == len(children) // 2:
                if len(children) % 2 == 0:
                    invis = self._node(None)
                    self._line(root, invis, weight=10, visible=False)

                    node = child.accept(self)
                    self._line(root, node)
                else:
                    node = child.accept(self)
                    self._line(root, node, weight=10)
            else:
                node = child.accept(self)
                self._line(root, node)

        return root

    def _node(self, msg: Optional[str]) -> int:
        identifier = self._counter
        self._counter += 1

        if msg:
            msg = json.dumps(msg)
            self._command(f"{identifier} [label={msg}]")
        else:
            self._command(f"{identifier} [style=invis]")

        return identifier

    def _line(
        self, start: int, end: int, weight: Optional[int] = None, visible: bool = True
    ):
        options = []
        if weight is not None:
            options.append(f"weight={weight}")
        if not visible:
            options.append("style=invis")

        if options:
            optstr = ", ".join(options)
            self._command(f"{start} -> {end} [{optstr}]")
        else:
            self._command(f"{start} -> {end}")

    def _command(self, command: str):
        print(f"{command};", file=self.output)

    def _raw(self, raw: str):
        print(raw, file=self.output)

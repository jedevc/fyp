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
    Node,
    PointerTypeNode,
    RefNode,
    SimpleTypeNode,
    SizeOfNode,
    SpecNode,
    SplitNode,
    StringValueNode,
    TemplateValueNode,
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
        raise NotImplementedError()

    def visit_type_pointer(self, node: PointerTypeNode):
        raise NotImplementedError()

    def visit_type_array(self, node: ArrayTypeNode):
        raise NotImplementedError()

    def visit_type_func(self, node: FuncTypeNode):
        raise NotImplementedError()

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
        if isinstance(node, StringValueNode):
            return self._node(repr(node.value))
        elif isinstance(node, IntValueNode):
            return self._node(str(node.value))
        elif isinstance(node, FloatValueNode):
            return self._node(f"{node.left}.{node.right}")
        elif isinstance(node, BoolValueNode):
            if node.value:
                return self._node("true")
            else:
                return self._node("false")
        elif isinstance(node, TemplateValueNode):
            return self._node(f"<{node.name}; {node.definition}>")
        else:
            raise RuntimeError()

    def visit_sizeof(self, node: SizeOfNode) -> int:
        cvar = ChunkVariable("", node.tp, None)
        return self._node(f"sizeof({cvar.typename()})")

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

        if msg is None:
            self._command(f"{identifier} [style=invis]")
        else:
            self._command(f"{identifier} [label={json.dumps(msg)}]")

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

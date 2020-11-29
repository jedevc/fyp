from typing import Dict, List

from ..block import (
    Array,
    Assignment,
    Block,
    Call,
    Deref,
    ExpressionStatement,
    Function,
    If,
    Ref,
    Value,
    Variable,
)
from ..chunk import Chunk, ChunkSet
from ..node import (
    ArrayNode,
    AssignmentNode,
    BlockNode,
    CallNode,
    DerefNode,
    ExpressionStatementNode,
    FunctionNode,
    IfNode,
    RefNode,
    SpecNode,
    ValueNode,
    VariableNode,
    Visitor,
)


class BlockifyVisitor(Visitor):
    def __init__(self, chunks: ChunkSet):
        super().__init__()
        self.chunks = chunks
        self.blocks: Dict[str, Block] = {}

    def result(self) -> List[Block]:
        return list(self.blocks.values())

    def visit_spec(self, node: SpecNode):
        self.blocks = {block.name: Block(block.name) for block in node.blocks}
        for block in node.blocks:
            block.accept(self)

    def visit_block(self, node: BlockNode):
        for statement in node.statements:
            stmt = statement.accept(self)
            self.blocks[node.name].add_statement(stmt)

    def visit_assignment(self, node: AssignmentNode) -> Assignment:
        return Assignment(node.target.accept(self), node.expression.accept(self))

    def visit_function(self, node: FunctionNode) -> Function:
        return Function(node.target, [expr.accept(self) for expr in node.arguments])

    def visit_value(self, node: ValueNode):
        return Value(node.value)

    def visit_variable(self, node: VariableNode) -> Variable:
        return Variable(self._lookup_var(node.name), node.name)

    def visit_ref(self, node: RefNode) -> Ref:
        return Ref(node.target.accept(self))

    def visit_deref(self, node: DerefNode) -> Deref:
        return Deref(node.target.accept(self))

    def visit_array(self, node: ArrayNode) -> Array:
        return Array(node.target.accept(self), node.index.accept(self))

    def visit_call(self, node: CallNode) -> Call:
        return Call(self.blocks[node.target])

    def visit_if(self, node: IfNode) -> If:
        return If(
            node.condition.accept(self), [stmt.accept(self) for stmt in node.statements]
        )

    def visit_exprstmt(self, node: ExpressionStatementNode) -> ExpressionStatement:
        return ExpressionStatement(node.expression.accept(self))

    def _lookup_var(self, name: str) -> Chunk:
        chunk = self.chunks.find(name)
        if chunk is None:
            # internal error, we should have applied a type check pass before this
            raise RuntimeError("variable was not found")
        return chunk

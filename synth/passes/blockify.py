from typing import Dict, List

from ..block import Assignment, Block, Call, Function, Value, Variable
from ..chunk import Chunk
from ..parser import (
    AssignmentNode,
    BlockNode,
    CallNode,
    FunctionNode,
    SpecNode,
    ValueNode,
    VariableNode,
    Visitor,
)


class BlockifyVisitor(Visitor):
    def __init__(self, chunks: List[Chunk]):
        super().__init__()
        self.chunks = chunks
        self.blocks: Dict[str, Block] = {}

    def _lookup_var(self, name: str) -> Chunk:
        # FIXME: this is terribly inefficient
        for chunk in self.chunks:
            if chunk.lookup(name):
                return chunk

        # FIXME: lovely way of panicking :)
        raise RuntimeError()

    def visit_spec(self, node: SpecNode) -> List[Block]:
        self.blocks = {block.label: Block() for block in node.blocks}
        for block in node.blocks:
            block.accept(self)
        return list(self.blocks.values())

    def visit_block(self, node: BlockNode):
        for statement in node.statements:
            stmt = statement.accept(self)
            self.blocks[node.label].add_statement(stmt)

    def visit_assignment(self, node: AssignmentNode) -> Assignment:
        return Assignment(
            self._lookup_var(node.name), node.name, node.expression.accept(self)
        )

    def visit_function(self, node: FunctionNode) -> Function:
        return Function(node.name, [expr.accept(self) for expr in node.arguments])

    def visit_value(self, node: ValueNode):
        return Value(node.value)

    def visit_variable(self, node: VariableNode) -> Variable:
        return Variable(self._lookup_var(node.target), node.target, node.address)

    def visit_call(self, node: CallNode) -> Call:
        return Call(self.blocks[node.target])

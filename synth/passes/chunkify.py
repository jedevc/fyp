from typing import List, Tuple

from ..parser import Visitor, SpecNode, ChunkNode, TypeNode, VariableNode

from ..chunk import Chunk, Variable


class ChunkifyVisitor(Visitor):
    def visit_spec(self, node: SpecNode) -> List[Chunk]:
        chunks = []
        for chunk in node.chunks:
            chunks.append(chunk.accept(self))
        return chunks

    def visit_chunk(self, node: ChunkNode) -> Chunk:
        variables = []
        for var in node.variables:
            variables.append(var.accept(self))
        return Chunk(variables)

    def visit_variable(self, node: VariableNode) -> Variable:
        return Variable(node.name, *node.vartype.accept(self))

    def visit_type(self, node: TypeNode) -> Tuple[str, int]:
        return node.base, node.size

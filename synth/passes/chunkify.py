from typing import List, Tuple

from ..parser import (
    ChunkNode,
    DeclarationNode,
    SpecNode,
    SpecialDeclarationNode,
    TypeNode,
    Visitor,
)
from ..parser.error import ProcessingError

from ..chunk import Chunk, ChunkConstraint, Variable


class ChunkifyVisitor(Visitor):
    def visit_spec(self, node: SpecNode) -> List[Chunk]:
        chunks = []
        for chunk in node.chunks:
            chunks.append(chunk.accept(self))
        return chunks

    def visit_chunk(self, node: ChunkNode) -> Chunk:
        constraint = ChunkConstraint()
        variables = []
        for var in node.variables:
            res = var.accept(self)
            if isinstance(res, ChunkConstraint):
                constraint = constraint.join(res)
            elif isinstance(res, Variable):
                variables.append(res)
            else:
                raise RuntimeError()

        return Chunk(variables, constraint)

    def visit_declaration(self, node: DeclarationNode) -> Variable:
        return Variable(node.name, *node.vartype.accept(self))

    def visit_special_declaration(
        self, node: SpecialDeclarationNode
    ) -> ChunkConstraint:
        if node.name == "eof":
            return ChunkConstraint(eof=True)
        else:
            raise ProcessingError(node, f"invalid special variable {node.name}")

    def visit_type(self, node: TypeNode) -> Tuple[str, int]:
        return node.base, node.size

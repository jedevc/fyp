from typing import Optional

from ..graph import Chunk, ChunkConstraint, ChunkVariable, Expression, merge_chunks
from ..node import (
    ChunkNode,
    DeclarationNode,
    ExternChunkNode,
    SpecialDeclarationNode,
    SpecNode,
    Visitor,
)
from .blockify import BlockifyExpressionVisitor, BlockifyVisitor
from .error import ProcessingError


class ChunkifyVisitor(Visitor[None]):
    def __init__(self):
        super().__init__()

        self.chunks = []
        self.extern = Chunk([])

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)

    def visit_chunk(self, node: ChunkNode):
        visitor = ChunkifyChunkVisitor()
        node.accept(visitor)
        self.chunks.append(visitor.chunk)

    def visit_extern(self, node: ExternChunkNode):
        visitor = ChunkifyChunkVisitor(allow_constraints=False)
        node.accept(visitor)
        self.extern = merge_chunks(self.extern, visitor.chunk)


class ChunkifyChunkVisitor(Visitor[None]):
    def __init__(self, allow_constraints: bool = True):
        super().__init__()

        self.chunk = Chunk([])
        self.allow_constraints = allow_constraints

    def visit_chunk(self, node: ChunkNode):
        for var in node.variables:
            var.accept(self)

    def visit_extern(self, node: ExternChunkNode):
        for var in node.variables:
            var.accept(self)

    def visit_declaration(self, node: DeclarationNode):
        if node.name in self.chunk:
            return

        init: Optional[Expression] = None
        if node.initial:
            # visit the expression without any chunks/extern
            init = node.initial.accept(
                BlockifyExpressionVisitor(BlockifyVisitor([], Chunk([])))
            )
        var = ChunkVariable(node.name, node.vartype, self.chunk, initial=init)
        self.chunk.add_variable(var)

    def visit_special_declaration(self, node: SpecialDeclarationNode):
        if not self.allow_constraints:
            raise ProcessingError(node, "cannot process chunk constraints here")

        if node.name == "eof":
            self.chunk.constraint = self.chunk.constraint.join(
                ChunkConstraint(eof=True)
            )
        else:
            raise ProcessingError(node, f"invalid special variable {node.name}")

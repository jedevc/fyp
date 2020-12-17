from ..graph import Chunk, ChunkConstraint, ChunkSet, ChunkVariable
from ..node import (
    ChunkNode,
    DeclarationNode,
    ExternChunkNode,
    SpecialDeclarationNode,
    SpecNode,
    Visitor,
)
from .error import ProcessingError


class ChunkifyVisitor(Visitor[None]):
    def __init__(self):
        super().__init__()

        self.chunks = []
        self.externs = []

        self._constraint = ChunkConstraint()
        self._variables = []

    def result(self) -> ChunkSet:
        return ChunkSet(self.externs, self.chunks)

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)

    def visit_chunk(self, node: ChunkNode):
        self._constraint = ChunkConstraint()
        self._variables = []
        for var in node.variables:
            var.accept(self)

        chunk = Chunk(self._variables, self._constraint)
        self.chunks.append(chunk)

    def visit_extern(self, node: ExternChunkNode):
        self._constraint = ChunkConstraint()
        self._variables = []
        for var in node.variables:
            var.accept(self)

        if not self._constraint.empty:
            raise ProcessingError(node, "cannot process extern chunk constraints")

        self.externs.extend(self._variables)

    def visit_declaration(self, node: DeclarationNode):
        var = ChunkVariable(node.name, node.vartype)
        self._variables.append(var)

    def visit_special_declaration(self, node: SpecialDeclarationNode):
        if node.name == "eof":
            self._constraint.join(ChunkConstraint(eof=True))
        else:
            raise ProcessingError(node, f"invalid special variable {node.name}")

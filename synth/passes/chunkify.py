from ..chunk import Chunk, ChunkConstraint, ChunkSet, Variable
from ..parser import (
    ChunkNode,
    DeclarationNode,
    ExternChunkNode,
    ProcessingError,
    SpecialDeclarationNode,
    SpecNode,
    Visitor,
)


class ChunkifyVisitor(Visitor):
    def __init__(self):
        super().__init__()

        self.chunks = []
        self.externs = []

    def result(self) -> ChunkSet:
        return ChunkSet(self.externs, self.chunks)

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)

    def visit_chunk(self, node: ChunkNode):
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

        chunk = Chunk(variables, constraint)
        self.chunks.append(chunk)

    def visit_extern(self, node: ExternChunkNode):
        variables = []
        for var in node.variables:
            res = var.accept(self)
            if isinstance(res, Variable):
                variables.append(res)
            elif isinstance(res, ChunkConstraint):
                raise ProcessingError(var, "cannot process extern chunk constraints")
            else:
                raise RuntimeError()

        self.externs.extend(variables)

    def visit_declaration(self, node: DeclarationNode) -> Variable:
        return Variable(node.name, node.vartype.base, node.vartype.size)

    def visit_special_declaration(
        self, node: SpecialDeclarationNode
    ) -> ChunkConstraint:
        if node.name == "eof":
            return ChunkConstraint(eof=True)
        else:
            raise ProcessingError(node, f"invalid special variable {node.name}")
